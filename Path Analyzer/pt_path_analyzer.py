#!/usr/bin/env python3
from __future__ import print_function

import argparse
import csv
import logging
import os
import sys
import re
from decimal import Decimal, ROUND_HALF_UP
from utilities import immutables as IM

try:
    import xlsxwriter
except ImportError:
    print(IM._XLSX_IMPORT_ERROR_)
    sys.exit(1)

ROW_LIMIT_XLSX = 1048576
IP_SCAN_ROOT = IM._IP_SCAN_ROOT_
REGISTER_TERMS = IM._REGISTER_TERMS_
MEMORY_TERMS = IM._MEMORY_TERMS_
LATCH_TERMS = IM._LATCH_TERMS_

_STARTPOINT_REGEX_ = IM._STARTPOINT_REGEX_
_ENDPOINT_REGEX_ = IM._ENDPOINT_REGEX_
_LAST_COMMON_PIN_REGEX_ = IM._LAST_COMMON_PIN_REGEX_
_PATH_GROUP_REGEX_ = IM._PATH_GROUP_REGEX_
_PATH_TYPE_REGEX_ = IM._PATH_TYPE_REGEX_
_CLOCK_EDGE_REGEX_ = IM._CLOCK_EDGE_REGEX_
_CLOCK_NETWORK_DELAY_REGEX_ = IM._CLOCK_NETWORK_DELAY_REGEX_
_CPPR_REGEX_ = IM._CPPR_REGEX_
_UNCERTAINTY_REGEX_ = IM._UNCERTAINTY_REGEX_
_LIBRARY_TIME_REGEX_ = IM._LIBRARY_TIME_REGEX_
_PATH_MARGIN_REGEX_ = IM._PATH_MARGIN_REGEX_
_SLACK_REGEX_ = IM._SLACK_REGEX_
_FLOAT_NUMBER_REGEX_ = IM._FLOAT_NUMBER_REGEX_
_POINT_HEADER_REGEX_ = IM._POINT_HEADER_REGEX_
_STAGE_LINE_REGEX_ = IM._STAGE_LINE_REGEX_
_CELL_REF_SUFFIX_REGEX_ = IM._CELL_REF_SUFFIX_REGEX_
_TRAILING_LOCATION_REGEX_ = IM._TRAILING_LOCATION_REGEX_
class XlsxSink(object):
    def __init__(self, out_path, enable_what_if=True):
        self.out_path = out_path
        self.enable_what_if = enable_what_if
        self.workbook = xlsxwriter.Workbook(out_path, {'constant_memory': True})
        self.status_fmt_green = self.workbook.add_format({'bg_color': '#00B050', 'font_color': '#FFFFFF', 'bold': True})
        self.status_fmt_yellow = self.workbook.add_format({'bg_color': '#FFD966', 'font_color': '#000000', 'bold': True})
        self.status_fmt_red = self.workbook.add_format({'bg_color': '#C00000', 'font_color': '#FFFFFF', 'bold': True})
        self.critical_fmt_red = self.workbook.add_format({'bg_color': '#C00000', 'font_color': '#FFFFFF', 'bold': True})
        self.header = list(IM._MAIN_HEADER_)
        self.header_index = {}
        i = 0
        while i < len(self.header):
            self.header_index[self.header[i]] = i
            i += 1

        special_for_interface = set(IM._SPECIAL_FOR_INTERFACE_)
        special_for_within_hm = set(IM._SPECIAL_FOR_WITHIN_HM_)
        special_io2io_for_top_to_hm = set(IM._SPECIAL_IO2IO_FOR_TOP_TO_HM_)
        self.header_by_base = {
            'within_hm': [h for h in self.header if h not in special_for_within_hm],
            'hm_to_hm': list(self.header),
            'top_to_hm': [h for h in self.header if h not in special_io2io_for_top_to_hm],
            'other': [h for h in self.header if h not in special_for_interface]
        }
        self.index_by_base = {}
        for base, hlist in self.header_by_base.items():
            self.index_by_base[base] = [self.header_index[h] for h in hlist]
        self.sheets = {}
        self.what_if_sheets = {}
        self.critical_tmp_path = '{0}.critical_paths.tsv'.format(out_path)
        self.critical_tmp_fp = open(self.critical_tmp_path, 'w')
        self.max_abs_slack = 0.0
        self.max_abs_skew = 0.0
        self.derived = {
            'reg2reg': {'count': 0, 'slack': [], 'skew': []},
            'mem2reg': {'count': 0, 'slack': [], 'skew': []},
            'reg2mem': {'count': 0, 'slack': [], 'skew': []},
            'mem2mem': {'count': 0, 'slack': [], 'skew': []},
            'reg2latch': {'count': 0, 'slack': [], 'skew': []},
            'latch2reg': {'count': 0, 'slack': [], 'skew': []}
        }

    def _matches_terms(self, text, terms):
        if not text:
            return False
        low = text.lower()
        for term in terms:
            if term and term.lower() in low:
                return True
        return False

    def _is_memory_cell(self, cell_name):
        return self._matches_terms(cell_name, MEMORY_TERMS)

    def _is_register_cell(self, cell_name):
        return self._matches_terms(cell_name, REGISTER_TERMS)

    def _is_latch_cell(self, cell_name):
        return self._matches_terms(cell_name, LATCH_TERMS)

    def _endpoint_kind(self, cell_name):
        # Classify strictly by library cell-name search terms from immutables.
        if self._is_memory_cell(cell_name):
            return 'mem'
        if self._is_latch_cell(cell_name):
            return 'latch'
        if self._is_register_cell(cell_name):
            return 'reg'
        # Keep reporting complete when cell type is unknown.
        return 'reg'

    def _classify_path_kind(self, start_cell, end_cell):
        s_kind = self._endpoint_kind(start_cell)
        e_kind = self._endpoint_kind(end_cell)
        if s_kind == 'mem' and e_kind == 'mem':
            return 'mem2mem'
        if s_kind == 'mem' and e_kind != 'mem':
            return 'mem2reg'
        if s_kind != 'mem' and e_kind == 'mem':
            return 'reg2mem'
        if s_kind == 'reg' and e_kind == 'latch':
            return 'reg2latch'
        if s_kind == 'latch' and e_kind == 'reg':
            return 'latch2reg'
        return 'reg2reg'

    def _sheet_base_name(self, category):
        c = (category or '').strip().lower()
        if c == IM._CAT_WITHIN_HM_.lower():
            return 'within_hm'
        if c == IM._CAT_HM_TO_HM_.lower():
            return 'hm_to_hm'
        if c == IM._CAT_TOP_TO_HM_.lower():
            return 'top_to_hm'
        return 'other'

    def _new_sheet_for_base(self, base, part):
        if part <= 1:
            name = base
        else:
            name = '{0}_{1}'.format(base, part)
        name = name[:31]
        sheet = self.workbook.add_worksheet(name)
        row = 0
        headers = self.header_by_base.get(base, self.header)
        col = 0
        for item in headers:
            sheet.write_string(row, col, item)
            col += 1
        return {'sheet': sheet, 'row': 1, 'part': part}

    def _get_sheet_state(self, category):
        base = self._sheet_base_name(category)
        state = self.sheets.get(base)
        if state is None:
            state = self._new_sheet_for_base(base, 1)
            self.sheets[base] = state
            return state

        if state['row'] >= ROW_LIMIT_XLSX:
            next_part = state['part'] + 1
            state = self._new_sheet_for_base(base, next_part)
            self.sheets[base] = state
        return state

    def write_row(self, category, row_values, start_cell=None, end_cell=None):
        sp = row_values[self.header_index['Startpoint']]
        ep = row_values[self.header_index['Endpoint']]
        slack = row_values[self.header_index['Slack']]
        skew = row_values[self.header_index['Skew']]
        kind = self._classify_path_kind(start_cell, end_cell)
        d = self.derived[kind]
        d['count'] += 1
        if isinstance(slack, (int, float)):
            d['slack'].append(float(slack))
            a = abs(float(slack))
            if a > self.max_abs_slack:
                self.max_abs_slack = a
        if isinstance(skew, (int, float)):
            d['skew'].append(float(skew))
            a = abs(float(skew))
            if a > self.max_abs_skew:
                self.max_abs_skew = a

        self.critical_tmp_fp.write('{0}\t{1}\t{2}\t{3}\t{4}\t{5}\t{6}\n'.format(
            str(sp).replace('\t', ' ').replace('\n', ' '),
            str(ep).replace('\t', ' ').replace('\n', ' '),
            str(start_cell or '').replace('\t', ' ').replace('\n', ' '),
            str(end_cell or '').replace('\t', ' ').replace('\n', ' '),
            kind,
            str(slack if isinstance(slack, (int, float)) else ''),
            str(skew if isinstance(skew, (int, float)) else '')
        ))

        state = self._get_sheet_state(category)
        sheet = state['sheet']
        row = state['row']
        base = self._sheet_base_name(category)
        idxs = self.index_by_base.get(base, list(range(0, len(row_values))))
        col = 0
        for idx in idxs:
            value = row_values[idx]
            if value is None:
                sheet.write_blank(row, col, None)
            elif isinstance(value, bool):
                sheet.write_boolean(row, col, value)
            elif isinstance(value, (int, float)):
                sheet.write_number(row, col, value)
            else:
                sheet.write_string(row, col, str(value))
            col += 1
        state['row'] = row + 1

    def _round_up_to_multiple(self, v, base):
        if base <= 0:
            return v
        if v <= 0:
            return float(base)
        q = int((v + base - 1.0e-12) / float(base))
        return float(q * base)

    def _round_up_int_multiple(self, v_int, base_int):
        if base_int <= 0:
            return v_int
        if v_int <= 0:
            return base_int
        return ((v_int + base_int - 1) // base_int) * base_int

    def _decimal_scale(self, values):
        # Keep precision bounded for stability/performance.
        max_decimals = 0
        for v in values:
            d = Decimal(str(v)).normalize()
            exp = -d.as_tuple().exponent
            if exp > max_decimals:
                max_decimals = exp
        if max_decimals > 6:
            max_decimals = 6
        return 10 ** max_decimals

    def _hist_bins(self, values, metric_kind):
        if not values:
            return []
        vmin = min(values)
        vmax = max(values)
        if vmax == vmin:
            vmax = vmin + 1.0
        max_abs = max(abs(vmin), abs(vmax))
        scale = self._decimal_scale(values)
        max_abs_int = int((Decimal(str(max_abs)) * Decimal(scale)).to_integral_value(rounding=ROUND_HALF_UP))
        if metric_kind == 'slack':
            ref_int = self._round_up_int_multiple(max_abs_int, 5)
            ref = float(Decimal(ref_int) / Decimal(scale))
            step = 0.10 * ref
        elif metric_kind == 'skew':
            ref_int = self._round_up_int_multiple(max_abs_int, 10)
            ref = float(Decimal(ref_int) / Decimal(scale))
            step = 0.10 * ref
        else:
            step = (vmax - vmin) / 20.0
        if step <= 0.0:
            step = 1.0

        bins = int((vmax - vmin) / step) + 1
        if bins < 5:
            bins = 5
        if bins > 120:
            bins = 120

        out = []
        i = 0
        while i < bins:
            lo = vmin + i * step
            hi = vmin + (i + 1) * step
            if i == bins - 1:
                cnt = len([x for x in values if x >= lo and x <= hi])
            else:
                cnt = len([x for x in values if x >= lo and x < hi])
            out.append((lo, hi, cnt))
            i += 1
        return out

    def _write_hist_block(self, sheet, start_row, start_col, title, values, metric_kind):
        sheet.write_string(start_row, start_col, title)
        sheet.write_string(start_row + 1, start_col + 0, 'Bin')
        sheet.write_string(start_row + 1, start_col + 1, 'Count')
        bins = self._hist_bins(values, metric_kind)
        r = start_row + 2
        for lo, hi, cnt in bins:
            sheet.write_string(r, start_col + 0, '{0:.4f} to {1:.4f}'.format(lo, hi))
            sheet.write_number(r, start_col + 1, cnt)
            r += 1
        if bins:
            chart = self.workbook.add_chart({'type': 'column'})
            chart.add_series({
                'name': title,
                'categories': [sheet.name, start_row + 2, start_col + 0, r - 1, start_col + 0],
                'values': [sheet.name, start_row + 2, start_col + 1, r - 1, start_col + 1],
            })
            chart.set_title({'name': title})
            chart.set_x_axis({'name': 'Bin'})
            chart.set_y_axis({'name': 'Count'})
            sheet.insert_chart(start_row + 1, start_col + 3, chart, {'x_scale': 1.0, 'y_scale': 0.8})

    def _write_derived_sheet(self):
        sheet = self.workbook.add_worksheet('Path Statistics')
        sheet.write_string(0, 0, 'Derived Path-Type Analysis')

        headers = ['Path Type', 'Count', 'Avg Slack', 'Worst Slack', 'Avg Skew', 'Max |Skew|', 'Critical']
        c = 0
        for h in headers:
            sheet.write_string(2, c, h)
            c += 1

        order = ['reg2reg', 'mem2reg', 'reg2mem', 'mem2mem', 'reg2latch', 'latch2reg']
        scores = {}
        stats = {}
        for k in order:
            d = self.derived[k]
            cnt = d['count']
            sl = d['slack']
            sk = d['skew']
            avg_sl = (sum(sl) / len(sl)) if sl else 0.0
            worst_sl = min(sl) if sl else 0.0
            avg_sk = (sum(sk) / len(sk)) if sk else 0.0
            max_abs_sk = max([abs(x) for x in sk]) if sk else 0.0
            score = max(0.0, -worst_sl) + abs(avg_sk)
            scores[k] = score if cnt > 0 else -1.0
            stats[k] = (cnt, avg_sl, worst_sl, avg_sk, max_abs_sk)

        max_score = max(scores.values()) if scores else -1.0
        critical = set([k for k, v in scores.items() if v == max_score and v > 0.0])

        row = 3
        for k in order:
            cnt, avg_sl, worst_sl, avg_sk, max_abs_sk = stats[k]
            is_critical = (k in critical)
            fmt = self.critical_fmt_red if is_critical else None
            sheet.write_string(row, 0, k, fmt)
            sheet.write_number(row, 1, cnt, fmt)
            sheet.write_number(row, 2, avg_sl, fmt)
            sheet.write_number(row, 3, worst_sl, fmt)
            sheet.write_number(row, 4, avg_sk, fmt)
            sheet.write_number(row, 5, max_abs_sk, fmt)
            sheet.write_string(row, 6, 'CRITICAL' if is_critical else '', fmt)
            row += 1

        chart = self.workbook.add_chart({'type': 'column'})
        dist_row_start = 3
        dist_row_end = dist_row_start + len(order) - 1
        chart.add_series({
            'name': 'Path Type Distribution',
            'categories': [sheet.name, dist_row_start, 0, dist_row_end, 0],
            'values': [sheet.name, dist_row_start, 1, dist_row_end, 1],
        })
        chart.set_title({'name': 'Path Type Distribution'})
        chart.set_x_axis({'name': 'Path Type'})
        chart.set_y_axis({'name': 'Count'})
        sheet.insert_chart(2, 8, chart, {'x_scale': 1.2, 'y_scale': 1.0})

        self._write_hist_block(sheet, 10, 0, 'reg2reg Slack Histogram', self.derived['reg2reg']['slack'], 'slack')
        self._write_hist_block(sheet, 34, 0, 'reg2reg Skew Histogram', self.derived['reg2reg']['skew'], 'skew')
        self._write_hist_block(sheet, 58, 0, 'mem2reg Slack Histogram', self.derived['mem2reg']['slack'], 'slack')
        self._write_hist_block(sheet, 82, 0, 'mem2reg Skew Histogram', self.derived['mem2reg']['skew'], 'skew')
        self._write_hist_block(sheet, 106, 0, 'reg2mem Slack Histogram', self.derived['reg2mem']['slack'], 'slack')
        self._write_hist_block(sheet, 130, 0, 'reg2mem Skew Histogram', self.derived['reg2mem']['skew'], 'skew')

    def _write_critical_pairs_sheet(self):
        self.critical_tmp_fp.flush()
        slack_cutoff_ns = -0.0100  # -10ps
        slack_thr = 0.10 * self.max_abs_slack if self.max_abs_slack > 0.0 else 0.0
        skew_thr = 0.10 * self.max_abs_skew if self.max_abs_skew > 0.0 else 0.0
        hier_pair_stats = {}

        def split_pin_instance_hier(pin_path):
            if not pin_path:
                return '', '', ''
            toks = pin_path.strip().split('/')
            if len(toks) < 2:
                return pin_path.strip(), '', ''
            pin = toks[-1]
            inst = toks[-2]
            hier = '/'.join(toks[:-2]) if len(toks) > 2 else ''
            return pin, inst, hier

        sheet = self.workbook.add_worksheet('Critical Paths')
        sheet.write_string(0, 0, 'Critical Start/End Pairs (High Slack and/or Skew)')
        sheet.write_string(0, 6, 'Slack cutoff (ns)')
        sheet.write_number(0, 7, slack_cutoff_ns)
        sheet.write_string(1, 0, 'Slack |threshold|')
        sheet.write_number(1, 1, slack_thr)
        sheet.write_string(1, 2, 'Skew |threshold|')
        sheet.write_number(1, 3, skew_thr)

        headers = [
            'Startpoint', 'Endpoint', 'Path Type',
            'Slack', 'Skew', '|Slack|', '|Skew|',
            'Critical Reason',
            'Start Pin', 'Start Instance', 'Start Hierarchy',
            'End Pin', 'End Instance', 'End Hierarchy',
            'Hierarchy Pair',
            'Start Cell', 'End Cell'
        ]
        c = 0
        for h in headers:
            sheet.write_string(3, c, h)
            c += 1

        row = 4
        with open(self.critical_tmp_path, 'r') as fin:
            reader = csv.reader(fin, delimiter='\t')
            for rec in reader:
                if len(rec) < 7:
                    continue
                sp, ep, sc, ec, kind, sl_s, sk_s = rec[:7]
                sl = safe_float(sl_s)
                sk = safe_float(sk_s)
                if sl is None or sl > slack_cutoff_ns:
                    continue
                abs_sl = abs(sl) if sl is not None else 0.0
                abs_sk = abs(sk) if sk is not None else 0.0
                high_sl = (sl is not None) and (abs_sl >= slack_thr)
                high_sk = (sk is not None) and (abs_sk >= skew_thr)
                if not (high_sl or high_sk):
                    continue

                if high_sl and high_sk:
                    reason = 'HIGH_SLACK_AND_SKEW'
                elif high_sl:
                    reason = 'HIGH_SLACK'
                else:
                    reason = 'HIGH_SKEW'

                s_pin, s_inst, s_hier = split_pin_instance_hier(sp)
                e_pin, e_inst, e_hier = split_pin_instance_hier(ep)
                pair = '{0} -> {1}'.format(s_hier, e_hier)

                key = (s_hier, e_hier)
                st = hier_pair_stats.get(key)
                if st is None:
                    st = {'count': 0, 'lowest_slack': None, 'highest_slack': None, 'max_abs_skew': 0.0}
                    hier_pair_stats[key] = st
                st['count'] += 1
                if sl is not None:
                    if st['lowest_slack'] is None or sl < st['lowest_slack']:
                        st['lowest_slack'] = sl
                    if st['highest_slack'] is None or sl > st['highest_slack']:
                        st['highest_slack'] = sl
                if abs_sk > st['max_abs_skew']:
                    st['max_abs_skew'] = abs_sk

                sheet.write_string(row, 0, sp)
                sheet.write_string(row, 1, ep)
                sheet.write_string(row, 2, kind)
                if sl is not None:
                    sheet.write_number(row, 3, sl)
                else:
                    sheet.write_string(row, 3, '')
                if sk is not None:
                    sheet.write_number(row, 4, sk)
                else:
                    sheet.write_string(row, 4, '')
                sheet.write_number(row, 5, abs_sl)
                sheet.write_number(row, 6, abs_sk)
                sheet.write_string(row, 7, reason)
                sheet.write_string(row, 8, s_pin)
                sheet.write_string(row, 9, s_inst)
                sheet.write_string(row, 10, s_hier)
                sheet.write_string(row, 11, e_pin)
                sheet.write_string(row, 12, e_inst)
                sheet.write_string(row, 13, e_hier)
                sheet.write_string(row, 14, pair)
                sheet.write_string(row, 15, sc)
                sheet.write_string(row, 16, ec)
                row += 1

        hs = self.workbook.add_worksheet('Hierarchy Connectivity')
        hs.write_string(0, 0, 'Unique Hierarchy Communication (Critical Paths)')
        hs_headers = ['Start Hierarchy', 'End Hierarchy', 'Critical Path Count', 'Lowest Slack', 'Highest Slack', 'Max |Skew|']
        i = 0
        for h in hs_headers:
            hs.write_string(2, i, h)
            i += 1

        entries = []
        for key, val in hier_pair_stats.items():
            entries.append((key[0], key[1], val['count'], val['lowest_slack'], val['highest_slack'], val['max_abs_skew']))
        entries.sort(key=lambda x: (-x[2], x[3] if x[3] is not None else 0.0))

        r = 3
        for sh, eh, cnt, lsl, hsl, msk in entries:
            hs.write_string(r, 0, sh)
            hs.write_string(r, 1, eh)
            hs.write_number(r, 2, cnt)
            if lsl is not None:
                hs.write_number(r, 3, lsl)
            else:
                hs.write_string(r, 3, '')
            if hsl is not None:
                hs.write_number(r, 4, hsl)
            else:
                hs.write_string(r, 4, '')
            hs.write_number(r, 5, msk if msk is not None else 0.0)
            r += 1

    def _new_what_if_sheet(self, base, headers):
        name = 'what_if_{0}'.format(base)
        name = name[:31]
        sheet = self.workbook.add_worksheet(name)
        col = 0
        for item in headers:
            sheet.write_string(0, col, item)
            col += 1
        status_col = None
        if 'Path Status' in headers:
            status_col = headers.index('Path Status')
        return {'sheet': sheet, 'row': 1, 'headers': headers, 'status_col': status_col}

    def write_what_if_row(self, category, row_dict):
        if not self.enable_what_if:
            return
        base = self._sheet_base_name(category)
        key = base

        if base == 'within_hm':
            headers = list(IM._WHATIF_HEADER_WITHIN_OR_OTHER_)
            values = [
                row_dict.get('startpoint'), row_dict.get('endpoint'),
                row_dict.get('output_port_hm'), row_dict.get('input_port_hm'),
                row_dict.get('data_required_time'), row_dict.get('data_arrival_time'),
                row_dict.get('slack'), row_dict.get('max_delay'),
                row_dict.get('internal_original_delay'), row_dict.get('internal_capped_delay'),
                row_dict.get('internal_post_removal'),
                row_dict.get('achievable_arrival'), row_dict.get('what_if_slack'),
                row_dict.get('arrival_post_removal'), row_dict.get('slack_post_removal'),
                row_dict.get('dominant'), row_dict.get('path_status')
            ]
        elif base == 'hm_to_hm':
            headers = list(IM._WHATIF_HEADER_HM_TO_HM_)
            values = [
                row_dict.get('startpoint'), row_dict.get('endpoint'),
                row_dict.get('output_port_hm'), row_dict.get('input_port_hm'),
                row_dict.get('data_required_time'), row_dict.get('data_arrival_time'),
                row_dict.get('slack'), row_dict.get('max_delay'),
                row_dict.get('reg2io_original'), row_dict.get('io2io_original'), row_dict.get('io2reg_original'),
                row_dict.get('reg2io_capped'), row_dict.get('io2io_capped'), row_dict.get('io2reg_capped'),
                row_dict.get('achievable_arrival'), row_dict.get('what_if_slack'),
                row_dict.get('reg2io_post_removal'), row_dict.get('io2io_post_removal'), row_dict.get('io2reg_post_removal'),
                row_dict.get('arrival_post_removal'), row_dict.get('slack_post_removal'),
                row_dict.get('dominant'), row_dict.get('path_status')
            ]
        elif base == 'top_to_hm':
            headers = list(IM._WHATIF_HEADER_TOP_TO_HM_)
            values = [
                row_dict.get('startpoint'), row_dict.get('endpoint'),
                row_dict.get('path_direction'),
                row_dict.get('output_port_hm') if row_dict.get('output_port_hm') != IM._NA_TEXT_ else row_dict.get('input_port_hm'),
                row_dict.get('data_required_time'), row_dict.get('data_arrival_time'),
                row_dict.get('slack'), row_dict.get('max_delay'),
                row_dict.get('seg_a_original'), row_dict.get('seg_b_original'),
                row_dict.get('seg_a_capped'), row_dict.get('seg_b_capped'),
                row_dict.get('achievable_arrival'), row_dict.get('what_if_slack'),
                row_dict.get('seg_a_post_removal'), row_dict.get('seg_b_post_removal'),
                row_dict.get('arrival_post_removal'), row_dict.get('slack_post_removal'),
                row_dict.get('dominant'), row_dict.get('path_status')
            ]
        else:
            headers = list(IM._WHATIF_HEADER_OTHER_)
            values = [
                row_dict.get('startpoint'), row_dict.get('endpoint'),
                row_dict.get('data_required_time'), row_dict.get('data_arrival_time'),
                row_dict.get('slack'), row_dict.get('max_delay'), row_dict.get('internal_original_delay'),
                row_dict.get('internal_capped_delay'), row_dict.get('achievable_arrival'),
                row_dict.get('what_if_slack'), row_dict.get('internal_post_removal'),
                row_dict.get('arrival_post_removal'), row_dict.get('slack_post_removal'),
                row_dict.get('path_status')
            ]

        state = self.what_if_sheets.get(key)
        if state is None:
            state = self._new_what_if_sheet(base, headers)
            self.what_if_sheets[key] = state

        sheet = state['sheet']
        row = state['row']
        col = 0
        for value in values:
            if value is None:
                sheet.write_blank(row, col, None)
            elif isinstance(value, bool):
                sheet.write_boolean(row, col, value)
            elif isinstance(value, (int, float)):
                sheet.write_number(row, col, value)
            else:
                sheet.write_string(row, col, str(value))
            col += 1

        sc = state.get('status_col')
        if sc is not None:
            status = row_dict.get('path_status')
            if status == IM._STATUS_FIXABLE_:
                sheet.write_string(row, sc, status, self.status_fmt_green)
            elif status == IM._STATUS_FIXABLE_BUF_REMOVE_:
                sheet.write_string(row, sc, status, self.status_fmt_yellow)
            elif status == IM._STATUS_UNFIXABLE_:
                sheet.write_string(row, sc, status, self.status_fmt_red)
        state['row'] = row + 1

    def close(self):
        self._write_derived_sheet()
        self._write_critical_pairs_sheet()
        self.critical_tmp_fp.close()
        try:
            os.remove(self.critical_tmp_path)
        except Exception:
            pass
        self.workbook.close()


def safe_float(token):
    try:
        return float(token)
    except Exception:
        return None


def leaf_name(path_text):
    text = path_text.strip('/')
    if not text:
        return ''
    parts = text.split('/')
    return parts[-1]


def instance_from_stage(stage_name):
    if '/' not in stage_name:
        return stage_name
    return stage_name.rsplit('/', 1)[0]


def is_integer_like(num_text):
    if '.' in num_text:
        return False
    if num_text.startswith('+') or num_text.startswith('-'):
        return num_text[1:].isdigit()
    return num_text.isdigit()


def normalize_type_text(type_text):
    t = type_text.strip().lower()
    t = t.replace('<', '').replace('>', '')
    return t


def classify_stage(stage_name, type_text, ip_leaf_names):
    t = normalize_type_text(type_text)
    low_name = stage_name.lower()

    if t == 'net' or low_name.endswith(' (net)'):
        return 'net'

    if t in ('hpin', 'hierarchical pin', 'hier pin'):
        return 'hpin'
    if t == 'ip':
        return 'ip'
    if t == 'cell':
        return 'cell'

    if type_text.strip().lower() == 'net':
        return 'net'

    if _CELL_REF_SUFFIX_REGEX_.search(type_text.strip()):
        return 'cell'

    inst = instance_from_stage(stage_name)
    leaf = leaf_name(inst).lower()
    if leaf in ip_leaf_names:
        return 'ip'

    return 'hpin'


def should_skip_instance(inst_name, type_text):
    low_inst = inst_name.lower()
    low_type = type_text.lower()

    for term in REGISTER_TERMS:
        if term in low_inst or term in low_type:
            return True

    for term in MEMORY_TERMS:
        if term in low_inst or term in low_type:
            return True

    if '/' not in inst_name:
        return True

    return False


def finalize_stage(path_acc, stage):
    if not stage:
        return

    stype = stage.get('stype')
    incr = stage.get('incr')
    fanout = stage.get('fanout')
    trans = stage.get('transition')
    cap = stage.get('cap')
    delta = stage.get('delta')
    row_type = 'net' if stype == 'net' else 'stage'

    path_acc['rows'].append({
        'type': row_type,
        'name': stage.get('stage_name', ''),
        'obj': stage.get('type_text', ''),
        'instance': stage.get('instance', ''),
        'incr': incr,
        'fanout': fanout,
        'cap': cap,
        'transition': trans,
        'delta': delta
    })

    if incr is not None:
        path_acc['total_data_delay'] += incr
        if stype == 'cell':
            inst_name = stage.get('instance')
            if inst_name:
                seen_count = path_acc['cell_pin_seen_count'].get(inst_name, 0)
                if seen_count == 0:
                    path_acc['total_net_delay'] += incr
                else:
                    path_acc['total_cell_delay'] += incr
                path_acc['cell_pin_seen_count'][inst_name] = seen_count + 1

    if fanout is not None and fanout > path_acc['max_fanout']:
        path_acc['max_fanout'] = fanout
    if trans is not None:
        if path_acc['max_transition'] is None or trans > path_acc['max_transition']:
            path_acc['max_transition'] = trans
    if cap is not None:
        if path_acc['max_cap'] is None or cap > path_acc['max_cap']:
            path_acc['max_cap'] = cap
    if delta is not None:
        path_acc['total_crosstalk'] += delta
        ad = abs(delta)
        if path_acc['max_crosstalk'] is None or ad > path_acc['max_crosstalk']:
            path_acc['max_crosstalk'] = ad

    if stype != 'cell':
        return

    inst = stage.get('instance')
    if not inst:
        return

    if should_skip_instance(inst, stage.get('type_text', '')):
        return

    if inst in path_acc['cell_seen']:
        return

    path_acc['cell_seen'].add(inst)
    path_acc['logic_depth'] += 1

    ccls = cell_class_from_instance_and_obj(inst, stage.get('type_text', ''))
    if ccls == 'buffer':
        path_acc['buffer_count'] += 1
    elif ccls == 'inverter':
        path_acc['inverter_count'] += 1


def parse_numeric_tokens(line):
    return _FLOAT_NUMBER_REGEX_.findall(line)


def strip_trailing_location(text):
    if text is None:
        return ''
    s = text.strip()
    return _TRAILING_LOCATION_REGEX_.sub('', s).strip()


def parse_stage_metrics_from_nums(nums):
    out = {'transition': None, 'delta': None, 'incr': None, 'path': None, 'voltage': None}
    if not nums:
        return out
    if len(nums) >= 1:
        out['voltage'] = safe_float(nums[-1])
    if len(nums) >= 2:
        out['path'] = safe_float(nums[-2])
    if len(nums) >= 3:
        out['incr'] = safe_float(nums[-3])
    if len(nums) >= 4:
        out['transition'] = safe_float(nums[0])
    if len(nums) >= 5:
        out['transition'] = safe_float(nums[1])
    if len(nums) >= 6:
        out['delta'] = safe_float(nums[-4])
    return out


def parse_point_columns(header_line):
    cols = []
    tokens = header_line.strip().split()
    for t in tokens[1:]:
        low = t.lower()
        if low in ('fanout', 'fo'):
            cols.append('fanout')
        elif low in ('incr',):
            cols.append('incr')
        elif low in ('path',):
            cols.append('path')
        elif low in ('trans', 'transition'):
            cols.append('transition')
        elif low in ('delta',):
            cols.append('delta')
        elif low in ('cap', 'capacitance'):
            cols.append('cap')
        else:
            cols.append('other')
    return cols


def fill_stage_from_nums(stage, nums, point_cols):
    if not nums:
        return

    idx = 0
    for col in point_cols:
        if idx >= len(nums):
            break

        if col == 'fanout':
            if stage.get('fanout') is None and is_integer_like(nums[idx]):
                v = safe_float(nums[idx])
                if v is not None:
                    stage['fanout'] = v
                idx += 1
            continue

        if col == 'incr':
            if stage.get('incr') is None:
                v = safe_float(nums[idx])
                if v is not None:
                    stage['incr'] = v
            idx += 1
            continue

        if col == 'transition':
            if stage.get('transition') is None:
                v = safe_float(nums[idx])
                if v is not None:
                    stage['transition'] = v
            idx += 1
            continue

        if col == 'delta':
            if stage.get('delta') is None:
                v = safe_float(nums[idx])
                if v is not None:
                    stage['delta'] = v
            idx += 1
            continue

        if col == 'cap':
            if stage.get('cap') is None:
                v = safe_float(nums[idx])
                if v is not None:
                    stage['cap'] = v
            idx += 1
            continue

        if col in ('path', 'other'):
            idx += 1

    if stage.get('incr') is None and len(nums) >= 1:
        if not (len(nums) == 1 and is_integer_like(nums[0])):
            v = safe_float(nums[0])
            if v is not None:
                stage['incr'] = v

    if stage.get('fanout') is None and len(nums) == 1 and is_integer_like(nums[0]):
        v = safe_float(nums[0])
        if v is not None:
            stage['fanout'] = v


def list_ip_leaf_names(root_path):
    names = set([x for x in os.listdir(root_path) if 'scratch' not in x])
    return set([x.lower() for x in names])


def first_matching_ip_name(path_text, ip_leaf_names):
    if not path_text:
        return None
    tokens = path_text.strip('/').split('/')
    for token in tokens:
        low = token.lower()
        if low in ip_leaf_names:
            return token
    return None


def classify_broad_path_type(startpoint, endpoint, ip_leaf_names):
    s_ip = first_matching_ip_name(startpoint, ip_leaf_names)
    e_ip = first_matching_ip_name(endpoint, ip_leaf_names)

    broad = IM._CAT_OTHER_
    direction = IM._CAT_OTHER_
    iface = IM._NA_TEXT_

    if s_ip and e_ip:
        if s_ip.lower() == e_ip.lower():
            broad = IM._CAT_WITHIN_HM_
            direction = IM._DIR_HM_INTERNAL_
            iface = s_ip
        else:
            broad = IM._CAT_HM_TO_HM_
            direction = IM._DIR_HM_TO_HM_
            iface = '{0}<->{1}'.format(s_ip, e_ip)
    elif s_ip and not e_ip:
        broad = IM._CAT_TOP_TO_HM_
        direction = IM._DIR_HM_TO_TOP_
    elif not s_ip and e_ip:
        broad = IM._CAT_TOP_TO_HM_
        direction = IM._DIR_TOP_TO_HM_

    return broad, direction, s_ip if s_ip else IM._NA_TEXT_, e_ip if e_ip else IM._NA_TEXT_, iface


def infer_category_from_report_name(report_name):
    if not report_name:
        return None
    toks = report_name.lower().split(':')
    hm_toks = [t for t in toks if t.startswith('hm_')]
    has_top = IM._TOP_TEXT_ in toks
    if has_top and hm_toks:
        hm = hm_toks[0]
        if toks[0].startswith('hm_'):
            return (IM._CAT_TOP_TO_HM_, IM._DIR_HM_TO_TOP_, hm, IM._TOP_TEXT_, hm)
        if toks[0] == IM._TOP_TEXT_:
            return (IM._CAT_TOP_TO_HM_, IM._DIR_TOP_TO_HM_, IM._TOP_TEXT_, hm, hm)
        return (IM._CAT_TOP_TO_HM_, IM._DIR_TOP_TO_HM_, IM._TOP_TEXT_, hm, hm)
    if len(hm_toks) >= 2:
        return (IM._CAT_HM_TO_HM_, IM._DIR_HM_TO_HM_, hm_toks[0], hm_toks[1], '{0}<->{1}'.format(hm_toks[0], hm_toks[1]))
    return None


def split_instance_pin(pin_name):
    idx = pin_name.rfind('/')
    if idx < 0:
        return '', pin_name
    return pin_name[:idx], pin_name[idx + 1:]


def root_token(path_text):
    if not path_text:
        return ''
    s = path_text.strip()
    if not s:
        return ''
    return s.split('/')[0]


_OUTPUT_PIN_TERMS_FALLBACK_ = ['clk_out', 'dout', 'dat', 'nz', 'q', 'z', 'x']


def is_output_pin_by_name_fallback(pin_name):
    p = (pin_name or '').strip().lower()
    if not p:
        return False
    for term in _OUTPUT_PIN_TERMS_FALLBACK_:
        if term in p:
            return True
    return False


def classify_rows(rows):
    has_any_net = False
    for rr in rows:
        if rr.get('type') == 'net':
            has_any_net = True
            break

    n = len(rows)
    i = 0
    while i < n:
        row = rows[i]
        if row.get('type') != 'stage':
            i += 1
            continue
        prev_is_net = i > 0 and rows[i - 1].get('type') == 'net'
        next_is_net = i < (n - 1) and rows[i + 1].get('type') == 'net'
        row['is_input_pin'] = prev_is_net
        row['is_output_pin'] = next_is_net
        if not prev_is_net and not next_is_net:
            # Fallback when net-based pin direction cannot be inferred.
            # If no net exists in the path report (or this row lacks net neighbors),
            # use pin-name terms to infer output; otherwise mark as input.
            _inst, pin = split_instance_pin(row.get('name', ''))
            out_guess = is_output_pin_by_name_fallback(pin)
            if (not has_any_net) or out_guess:
                row['is_output_pin'] = out_guess
                row['is_input_pin'] = not out_guess
        row['is_hpin'] = prev_is_net and next_is_net
        i += 1


def find_hm_name_exact(row, hm_names):
    obj = row.get('obj', '').strip()
    name = row.get('name', '').strip()

    def canonical(token):
        t = token.lower()
        if not t:
            return ''
        if t in hm_names:
            return token
        for hm in hm_names:
            if t.startswith(hm) or hm.startswith(t):
                return hm
        if t.startswith('hm_'):
            return token
        return ''

    c = canonical(obj)
    if c:
        return c

    parts = name.split('/')
    for p in parts:
        c = canonical(p)
        if c:
            return c
    return ''


def find_hm_hpin_list(rows, hm_names):
    hpins = []
    i = 0
    while i < len(rows):
        row = rows[i]
        if row.get('type') != 'stage':
            i += 1
            continue
        if not row.get('is_hpin'):
            i += 1
            continue
        hm = find_hm_name_exact(row, hm_names)
        if hm:
            hpins.append((i, hm))
        i += 1
    return hpins


def empty_segment_result():
    return {
        'stage_delay': 0.0,
        'net_delay': 0.0,
        'stage_plus_net_delay': 0.0,
        'logic_depth': 0,
        'pure_comb_depth': 0,
        'buffer_count': 0,
        'inverter_count': 0,
        'b2b_inv_pair_count': 0,
        'top_cap': None,
        'top_cell_delay': None,
        'top_net_delay': None,
        'max_fanout': None,
        'capped_total_delay': 0.0,
        'capped_after_bufinv_removal_delay': 0.0
    }


def is_data_buffer_text(text):
    t = text.lower()
    if '_cbuf' in t:
        return False
    return '_buf' in t


def is_data_inverter_text(text):
    t = text.lower()
    if '_cinv' in t:
        return False
    return '_inv' in t


def cell_class_from_instance_and_obj(inst, obj):
    inst_base = leaf_name(inst)
    combined = '{0} {1}'.format(inst_base, obj)
    low = combined.lower()

    if '_cbuf' in low or '_cinv' in low:
        return ''

    if is_data_buffer_text(combined):
        return 'buffer'

    if is_data_inverter_text(combined):
        return 'inverter'

    return ''


def get_cell_class_for_row(row):
    inst = row.get('instance', '')
    obj = row.get('obj', '')
    return cell_class_from_instance_and_obj(inst, obj)


def normalize_endpoint_ref(endpoint_text):
    ref = (endpoint_text or '').strip()
    if not ref:
        return ''
    # Startpoint/Endpoint lines may include trailing annotations.
    return ref.split()[0]


def _first_cell_obj_for_instance(rows, inst_name):
    if not inst_name:
        return ''
    for row in rows:
        if row.get('type') != 'stage':
            continue
        if (row.get('instance') or '').strip() != inst_name:
            continue
        obj = (row.get('obj') or '').strip()
        if not obj or obj.lower() == 'net':
            continue
        return obj
    return ''


def cell_name_for_pin(rows, pin_name):
    ref = normalize_endpoint_ref(pin_name)
    if not ref:
        return ''

    # Primary: exact stage pin match.
    for row in rows:
        if row.get('type') != 'stage':
            continue
        if (row.get('name') or '').strip() != ref:
            continue
        obj = (row.get('obj') or '').strip()
        if not obj or obj.lower() == 'net':
            continue
        return obj

    # Fallback: Startpoint/Endpoint can be instance-only (no pin).
    # In that case resolve by matching stage.instance to the endpoint instance.
    obj = _first_cell_obj_for_instance(rows, ref)
    if obj:
        return obj

    # Final fallback: infer instance from pin-like endpoint and match by instance.
    inst, _pin = split_instance_pin(ref)
    return _first_cell_obj_for_instance(rows, inst)


def endpoint_kind_from_cell(cell_name):
    low = (cell_name or '').lower()
    for term in MEMORY_TERMS:
        if term and term.lower() in low:
            return 'mem'
    for term in LATCH_TERMS:
        if term and term.lower() in low:
            return 'latch'
    for term in REGISTER_TERMS:
        if term and term.lower() in low:
            return 'reg'
    return 'reg'


def classify_path_kind_from_cells(start_cell, end_cell):
    s_kind = endpoint_kind_from_cell(start_cell)
    e_kind = endpoint_kind_from_cell(end_cell)
    if s_kind == 'mem' and e_kind == 'mem':
        return 'mem2mem'
    if s_kind == 'mem' and e_kind != 'mem':
        return 'mem2reg'
    if s_kind != 'mem' and e_kind == 'mem':
        return 'reg2mem'
    if s_kind == 'reg' and e_kind == 'latch':
        return 'reg2latch'
    if s_kind == 'latch' and e_kind == 'reg':
        return 'latch2reg'
    return 'reg2reg'


def mine_segment(rows, start_idx, end_idx, start_reg_inst, end_reg_inst, max_delay):
    result = empty_segment_result()
    if start_idx is None or end_idx is None or start_idx > end_idx:
        return result

    total_stage_delay = 0.0
    total_net_delay = 0.0
    max_cap = None
    max_fanout = None
    max_stage_delay = None
    max_net_delay = None

    logic_instances = set()
    ordered_instances = []
    seen_ordered = set()
    inst_info = {}

    def ensure_inst(inst):
        if inst not in inst_info:
            inst_info[inst] = {'stage': 0.0, 'net': 0.0, 'capped_stage': 0.0, 'class': ''}

    i = start_idx
    while i <= end_idx:
        row = rows[i]
        if row.get('type') == 'net':
            cap = row.get('cap')
            fanout = row.get('fanout')
            if cap is not None and (max_cap is None or cap > max_cap):
                max_cap = cap
            if fanout is not None and (max_fanout is None or fanout > max_fanout):
                max_fanout = fanout
            i += 1
            continue

        if row.get('type') != 'stage':
            i += 1
            continue

        if row.get('is_hpin'):
            i += 1
            continue

        inst = row.get('instance', '')
        if not inst:
            i += 1
            continue

        ensure_inst(inst)
        cell_class = get_cell_class_for_row(row)
        if cell_class and not inst_info[inst]['class']:
            inst_info[inst]['class'] = cell_class

        if inst != start_reg_inst and inst != end_reg_inst and not should_skip_instance(inst, row.get('obj', '')):
            logic_instances.add(inst)
            if inst not in seen_ordered:
                ordered_instances.append(inst)
                seen_ordered.add(inst)

        incr = row.get('incr')
        if incr is None:
            incr = 0.0

        if row.get('is_output_pin'):
            total_stage_delay += incr
            inst_info[inst]['stage'] += incr
            if max_delay is None:
                inst_info[inst]['capped_stage'] += incr
            else:
                inst_info[inst]['capped_stage'] += min(incr, max_delay)
            if max_stage_delay is None or incr > max_stage_delay:
                max_stage_delay = incr

        if row.get('is_input_pin'):
            total_net_delay += incr
            inst_info[inst]['net'] += incr
            if max_net_delay is None or incr > max_net_delay:
                max_net_delay = incr

        i += 1

    buffer_instances = set()
    inverter_instances = set()
    j = 0
    removable_inverters = set()

    while j < len(ordered_instances) - 1:
        i1 = ordered_instances[j]
        i2 = ordered_instances[j + 1]
        c1 = inst_info.get(i1, {}).get('class', '')
        c2 = inst_info.get(i2, {}).get('class', '')
        if c1 == 'inverter' and c2 == 'inverter':
            removable_inverters.add(i1)
            removable_inverters.add(i2)
            result['b2b_inv_pair_count'] += 1
            j += 2
        else:
            j += 1

    capped_total = 0.0
    removable_delay = 0.0
    for inst, info in inst_info.items():
        cls = info.get('class', '')
        if cls == 'buffer':
            buffer_instances.add(inst)
        elif cls == 'inverter':
            inverter_instances.add(inst)
        capped_total += info['capped_stage'] + info['net']
        if cls == 'buffer' or inst in removable_inverters:
            removable_delay += info['capped_stage'] + info['net']

    result['stage_delay'] = total_stage_delay
    result['net_delay'] = total_net_delay
    result['stage_plus_net_delay'] = total_stage_delay + total_net_delay
    result['logic_depth'] = len(logic_instances)
    result['buffer_count'] = len(buffer_instances)
    result['inverter_count'] = len(inverter_instances)
    pure = result['logic_depth'] - result['buffer_count'] - result['inverter_count']
    result['pure_comb_depth'] = pure if pure > 0 else 0
    result['top_cap'] = max_cap
    result['top_cell_delay'] = max_stage_delay
    result['top_net_delay'] = max_net_delay
    result['max_fanout'] = max_fanout
    result['capped_total_delay'] = capped_total
    v = capped_total - removable_delay
    result['capped_after_bufinv_removal_delay'] = v if v > 0.0 else 0.0
    return result


def compute_segmentation(path_acc, hm_names, max_delay):
    rows = path_acc.get('rows', [])
    classify_rows(rows)
    start_inst, _ = split_instance_pin(path_acc.get('startpoint') or '')
    end_inst, _ = split_instance_pin(path_acc.get('endpoint') or '')
    broad = path_acc.get('broad_type', 'Other')
    direction = path_acc.get('path_direction', 'Other')

    seg = {
        'reg2io': empty_segment_result(),
        'io2io': empty_segment_result(),
        'io2reg': empty_segment_result(),
        'output_port_pin': 'NA',
        'input_port_pin': 'NA',
        'output_port_hm': 'NA',
        'input_port_hm': 'NA',
        'middle_ips': [],
        'detected_broad': broad,
        'detected_direction': direction
    }

    hpins = find_hm_hpin_list(rows, hm_names)
    all_hpins = []
    true_bounds = []
    i = 0
    while i < len(rows):
        r = rows[i]
        if r.get('type') == 'stage':
            if r.get('is_hpin'):
                hm = find_hm_name_exact(r, hm_names)
                all_hpins.append((i, hm))
            # Boundary crossing detection is based on exact HM object/cell name.
            obj = (r.get('obj') or '').strip()
            if obj and obj.lower() in hm_names:
                true_bounds.append((i, obj))
        i += 1
    last_idx = len(rows) - 1

    forced = infer_category_from_report_name(path_acc.get('report_name', ''))

    # Compress repeated exact-boundary HM objects into transition points.
    true_seq = []
    for idx, hm in true_bounds:
        if not true_seq or true_seq[-1][1].lower() != hm.lower():
            true_seq.append((idx, hm))

    # Primary rule: classify by true HM/IP boundary crossings.
    if len(true_seq) >= 2:
        out_idx, out_hm = true_seq[0]
        in_idx, in_hm = true_seq[-1]
        if in_hm.lower() != out_hm.lower():
            seg['output_port_pin'] = rows[out_idx].get('name', 'NA')
            seg['input_port_pin'] = rows[in_idx].get('name', 'NA')
            seg['output_port_hm'] = out_hm
            seg['input_port_hm'] = in_hm
            mids = []
            seen_mid = set()
            for _idx, hm in true_seq[1:-1]:
                hl = hm.lower()
                if hl == out_hm.lower() or hl == in_hm.lower():
                    continue
                if hl in seen_mid:
                    continue
                seen_mid.add(hl)
                mids.append(hm)
            seg['middle_ips'] = mids
            seg['reg2io'] = mine_segment(rows, 0, out_idx, start_inst, end_inst, max_delay)
            seg['io2io'] = mine_segment(rows, out_idx, in_idx, start_inst, end_inst, max_delay)
            seg['io2reg'] = mine_segment(rows, in_idx, last_idx, start_inst, end_inst, max_delay)
            seg['detected_broad'] = 'HM to HM'
            seg['detected_direction'] = 'HM to HM'
            return seg

    if len(true_seq) == 1:
        idx, hm = true_seq[0]
        det_dir = 'Top to HM'
        if forced and forced[0] == 'Top to HM':
            det_dir = forced[1]
        else:
            bname = rows[idx].get('name', '')
            broot = root_token(bname)
            sroot = root_token(path_acc.get('startpoint') or '')
            eroot = root_token(path_acc.get('endpoint') or '')
            if broot and sroot and broot == sroot and (not eroot or broot != eroot):
                det_dir = 'HM to Top'
            elif broot and eroot and broot == eroot and (not sroot or broot != sroot):
                det_dir = 'Top to HM'
            else:
                # Boundary near start implies path exits HM; near end implies enters HM.
                if last_idx > 0 and (float(idx) / float(last_idx)) <= 0.5:
                    det_dir = 'HM to Top'
                else:
                    det_dir = 'Top to HM'

        if det_dir == 'HM to Top':
            seg['output_port_hm'] = hm
            seg['output_port_pin'] = rows[idx].get('name', 'NA')
        else:
            seg['input_port_hm'] = hm
            seg['input_port_pin'] = rows[idx].get('name', 'NA')
        seg['reg2io'] = mine_segment(rows, 0, idx, start_inst, end_inst, max_delay)
        seg['io2reg'] = mine_segment(rows, idx, last_idx, start_inst, end_inst, max_delay)
        seg['detected_broad'] = 'Top to HM'
        seg['detected_direction'] = det_dir
        return seg

    # Fallback to legacy heuristics when exact HM boundary is absent.
    if broad == 'HM to HM' and len(hpins) >= 2:
        out_idx, out_hm = hpins[0]
        in_idx = None
        in_hm = ''
        for idx, hm in hpins[1:]:
            if hm != out_hm:
                in_idx = idx
                in_hm = hm
                break
        if in_idx is None:
            in_idx, in_hm = hpins[1]
        seg['output_port_pin'] = rows[out_idx].get('name', 'NA')
        seg['input_port_pin'] = rows[in_idx].get('name', 'NA')
        seg['output_port_hm'] = out_hm
        seg['input_port_hm'] = in_hm
        seg['reg2io'] = mine_segment(rows, 0, out_idx, start_inst, end_inst, max_delay)
        seg['io2io'] = mine_segment(rows, out_idx, in_idx, start_inst, end_inst, max_delay)
        seg['io2reg'] = mine_segment(rows, in_idx, last_idx, start_inst, end_inst, max_delay)
        seg['detected_broad'] = 'HM to HM'
        seg['detected_direction'] = 'HM to HM'
    elif broad == 'Top to HM' and len(hpins) >= 1:
        idx, hm = hpins[0]
        pin = rows[idx].get('name', 'NA')
        if direction == 'Top to HM':
            seg['input_port_hm'] = hm
            seg['input_port_pin'] = pin
            seg['detected_direction'] = 'Top to HM'
        else:
            seg['output_port_hm'] = hm
            seg['output_port_pin'] = pin
            seg['detected_direction'] = 'HM to Top'
        seg['reg2io'] = mine_segment(rows, 0, idx, start_inst, end_inst, max_delay)
        seg['io2reg'] = mine_segment(rows, idx, last_idx, start_inst, end_inst, max_delay)
        seg['detected_broad'] = 'Top to HM'
    else:
        seg['io2io'] = mine_segment(rows, 0, last_idx, start_inst, end_inst, max_delay)
        seg['detected_broad'] = 'Within HM'
        seg['detected_direction'] = 'HM Internal'

    forced = infer_category_from_report_name(path_acc.get('report_name', ''))
    if forced and forced[0] == 'Top to HM':
        seg['detected_broad'] = 'Top to HM'
        seg['detected_direction'] = forced[1]
        if len(hpins) >= 1:
            if forced[1] == 'HM to Top':
                idx, hm = hpins[-1]
                seg['output_port_hm'] = hm
                seg['output_port_pin'] = rows[idx].get('name', 'NA')
                seg['reg2io'] = mine_segment(rows, 0, idx, start_inst, end_inst, max_delay)
                seg['io2reg'] = mine_segment(rows, idx, last_idx, start_inst, end_inst, max_delay)
            else:
                idx, hm = hpins[0]
                seg['input_port_hm'] = hm
                seg['input_port_pin'] = rows[idx].get('name', 'NA')
                seg['reg2io'] = mine_segment(rows, 0, idx, start_inst, end_inst, max_delay)
                seg['io2reg'] = mine_segment(rows, idx, last_idx, start_inst, end_inst, max_delay)
        elif len(all_hpins) >= 1:
            if forced[1] == 'HM to Top':
                idx, hm = all_hpins[-1]
                seg['output_port_hm'] = hm if hm else 'NA'
                seg['output_port_pin'] = rows[idx].get('name', 'NA')
            else:
                idx, hm = all_hpins[0]
                seg['input_port_hm'] = hm if hm else 'NA'
                seg['input_port_pin'] = rows[idx].get('name', 'NA')

    if seg.get('detected_broad') == 'Other':
        s = (path_acc.get('startpoint') or '').strip()
        e = (path_acc.get('endpoint') or '').strip()
        if s and e:
            s0 = s.split('/')[0]
            e0 = e.split('/')[0]
            if s0 and s0 == e0:
                seg['detected_broad'] = 'Within HM'
                seg['detected_direction'] = 'HM Internal'
                seg['output_port_hm'] = s0
                seg['input_port_hm'] = e0

    return seg


def build_what_if_summary(path_acc, seg, max_delay):
    reg2io = seg['reg2io']
    io2io = seg['io2io']
    io2reg = seg['io2reg']
    total_orig = reg2io['stage_plus_net_delay'] + io2io['stage_plus_net_delay'] + io2reg['stage_plus_net_delay']
    achievable = reg2io['capped_total_delay'] + io2io['capped_total_delay'] + io2reg['capped_total_delay']
    post = reg2io['capped_after_bufinv_removal_delay'] + io2io['capped_after_bufinv_removal_delay'] + io2reg['capped_after_bufinv_removal_delay']

    req = path_acc.get('data_required_time')
    what_if_slack = None
    post_slack = None

    if max_delay is None:
        status = IM._STATUS_SKIPPED_
    else:
        if req is not None:
            what_if_slack = req - achievable
            post_slack = req - post

        status = IM._STATUS_UNFIXABLE_
        if what_if_slack is not None and what_if_slack >= 0.0:
            status = IM._STATUS_FIXABLE_
        elif post_slack is not None and post_slack >= 0.0:
            status = IM._STATUS_FIXABLE_BUF_REMOVE_

    reg2io_cap = reg2io['capped_total_delay']
    io2io_cap = io2io['capped_total_delay']
    io2reg_cap = io2reg['capped_total_delay']
    if reg2io_cap >= io2io_cap and reg2io_cap >= io2reg_cap:
        dominant = seg.get('output_port_hm', 'NA')
    elif io2io_cap >= reg2io_cap and io2io_cap >= io2reg_cap:
        dominant = IM._INTERFACE_DOMINANT_TEXT_
    else:
        dominant = seg.get('input_port_hm', 'NA')

    return {
        'max_delay': max_delay,
        'total_original': total_orig,
        'achievable_arrival': achievable,
        'what_if_slack': what_if_slack,
        'arrival_post_removal': post,
        'slack_post_removal': post_slack,
        'path_status': status,
        'dominant': dominant
    }


def iter_report_files(input_path):
    if os.path.isfile(input_path):
        yield input_path
        return

    for dirpath, _dirnames, filenames in os.walk(input_path):
        for name in filenames:
            low = name.lower()
            if low.endswith('.rpt') or low.endswith('.txt') or low.endswith('.report'):
                yield os.path.join(dirpath, name)


def new_path_acc():
    return {
        'startpoint': None,
        'endpoint': None,
        'last_common_pin': None,
        'path_group': None,
        'path_type': None,
        'launch_clock': None,
        'capture_clock': None,
        'launch_edge': None,
        'capture_edge': None,
        'launch_source_delay': None,
        'capture_source_delay': None,
        'launch_net_delay': None,
        'capture_net_delay': None,
        'cppr': 0.0,
        'uncertainty': None,
        'lib_time': None,
        'path_margin': None,
        'data_required_time': None,
        'data_arrival_time': None,
        'slack': None,
        'clock_edge_values': [],
        'clock_names': [],
        'clock_source_values': [],
        'clock_net_values': [],

        'cell_seen': set(),
        'logic_depth': 0,
        'buffer_count': 0,
        'inverter_count': 0,
        'total_data_delay': 0.0,
        'total_net_delay': 0.0,
        'total_cell_delay': 0.0,
        'cell_pin_seen_count': {},
        'max_transition': None,
        'max_fanout': 0.0,
        'max_cap': None,
        'max_crosstalk': None,
        'total_crosstalk': 0.0,
        'rows': [],
        'broad_type': 'Other',
        'path_direction': 'Other',
        'start_hm_ip': 'NA',
        'end_hm_ip': 'NA',
        'hm_interface': 'NA',
        'report_name': '',
    }


def write_path_row(path_acc, sink, ip_leaf_names, max_delay, analysis_type):
    launch_src = path_acc.get('launch_source_delay')
    capture_src = path_acc.get('capture_source_delay')
    launch_nd = path_acc.get('launch_net_delay')
    capture_nd = path_acc.get('capture_net_delay')
    cppr = abs(path_acc['cppr']) if path_acc.get('cppr') is not None else 0.0

    # Latency = Source Delay + Network Delay. Missing terms are treated as 0.
    launch_latency = (launch_src if launch_src is not None else 0.0) + (launch_nd if launch_nd is not None else 0.0)
    capture_latency = (capture_src if capture_src is not None else 0.0) + (capture_nd if capture_nd is not None else 0.0)

    # User-required sign convention:
    # setup: Launch - Capture - CPPR
    # hold : Capture - Launch - CPPR
    if analysis_type == 'setup':
        skew = launch_latency - capture_latency - cppr
    else:
        skew = capture_latency - launch_latency - cppr

    launch_edge = path_acc['launch_edge']
    capture_edge = path_acc['capture_edge']

    clock_period = None
    if None not in (launch_edge, capture_edge):
        clock_period = capture_edge - launch_edge
        if clock_period == 0.0:
            clock_period = capture_edge

    inv_count = path_acc['inverter_count']
    buf_count = path_acc['buffer_count']
    logic_depth = path_acc['logic_depth']
    b2b_inv = inv_count // 2
    logic_inversion = (inv_count % 2) == 1
    pure_comb_depth = logic_depth - buf_count - inv_count + (inv_count % 2)
    if pure_comb_depth < 0:
        pure_comb_depth = 0

    start_cell = cell_name_for_pin(path_acc.get('rows', []), path_acc.get('startpoint'))
    end_cell = cell_name_for_pin(path_acc.get('rows', []), path_acc.get('endpoint'))
    path_type_class = classify_path_kind_from_cells(start_cell, end_cell)

    broad, direction, start_ip, end_ip, iface = classify_broad_path_type(path_acc['startpoint'], path_acc['endpoint'], ip_leaf_names)
    path_acc['broad_type'] = broad
    path_acc['path_direction'] = direction
    path_acc['start_hm_ip'] = start_ip
    path_acc['end_hm_ip'] = end_ip
    path_acc['hm_interface'] = iface

    seg = compute_segmentation(path_acc, ip_leaf_names, max_delay)
    if seg.get('detected_broad') and seg.get('detected_broad') != 'Other':
        broad = seg.get('detected_broad')
        direction = seg.get('detected_direction', direction)
        if broad == 'HM to HM':
            if seg.get('output_port_hm') and seg.get('output_port_hm') != 'NA':
                start_ip = seg.get('output_port_hm')
            if seg.get('input_port_hm') and seg.get('input_port_hm') != 'NA':
                end_ip = seg.get('input_port_hm')
        elif broad == 'Top to HM':
            if direction == 'HM to Top':
                if seg.get('output_port_hm') and seg.get('output_port_hm') != 'NA':
                    start_ip = seg.get('output_port_hm')
                end_ip = 'top'
            else:
                start_ip = 'top'
                if seg.get('input_port_hm') and seg.get('input_port_hm') != 'NA':
                    end_ip = seg.get('input_port_hm')
        if seg.get('output_port_hm') != 'NA' and seg.get('input_port_hm') != 'NA':
            iface = '{0}<->{1}'.format(seg.get('output_port_hm'), seg.get('input_port_hm'))
        elif seg.get('output_port_hm') != 'NA':
            iface = seg.get('output_port_hm')
        elif seg.get('input_port_hm') != 'NA':
            iface = seg.get('input_port_hm')
    middle_ips = seg.get('middle_ips') or []
    middle_ips_s = '|'.join(middle_ips) if middle_ips else 'NA'
    inferred = infer_category_from_report_name(path_acc.get('report_name', ''))
    if inferred:
        # Report name convention can explicitly encode category and direction.
        if inferred[0] == 'Top to HM':
            broad, direction, start_ip, end_ip, iface = inferred
        elif broad == 'Other':
            broad, direction, start_ip, end_ip, iface = inferred
    what_if = build_what_if_summary(path_acc, seg, max_delay)
    top_cell_delay = None
    top_net_delay = None
    for v in [seg['reg2io'].get('top_cell_delay'), seg['io2io'].get('top_cell_delay'), seg['io2reg'].get('top_cell_delay')]:
        if v is None:
            continue
        if top_cell_delay is None or v > top_cell_delay:
            top_cell_delay = v
    for v in [seg['reg2io'].get('top_net_delay'), seg['io2io'].get('top_net_delay'), seg['io2reg'].get('top_net_delay')]:
        if v is None:
            continue
        if top_net_delay is None or v > top_net_delay:
            top_net_delay = v

    row = [
        path_acc['startpoint'],
        path_acc['endpoint'],
        path_acc['last_common_pin'],
        path_acc['path_group'],
        path_type_class,
        start_ip,
        end_ip,
        iface,
        middle_ips_s,
        seg.get('output_port_pin'),
        seg.get('output_port_hm'),
        seg.get('input_port_pin'),
        seg.get('input_port_hm'),
        path_acc['launch_clock'],
        path_acc['capture_clock'],
        launch_latency,
        capture_latency,
        clock_period,
        path_acc['uncertainty'],
        path_acc['cppr'],
        path_acc['lib_time'],
        path_acc['path_margin'],
        path_acc['data_required_time'],
        path_acc['data_arrival_time'],
        path_acc['slack'],
        skew,
        logic_depth,
        buf_count,
        inv_count,
        b2b_inv,
        logic_inversion,
        pure_comb_depth,
        path_acc['total_data_delay'],
        path_acc['total_net_delay'],
        path_acc['total_cell_delay'],
        path_acc['max_crosstalk'] if path_acc['max_crosstalk'] is not None else 'NA',
        path_acc['total_crosstalk'] if path_acc['max_crosstalk'] is not None else 'NA',
        path_acc['max_transition'] if path_acc['max_transition'] is not None else 'NA',
        top_cell_delay if top_cell_delay is not None else 'NA',
        top_net_delay if top_net_delay is not None else 'NA',
        seg['reg2io']['stage_plus_net_delay'],
        seg['io2io']['stage_plus_net_delay'],
        seg['io2reg']['stage_plus_net_delay'],
        seg['reg2io']['logic_depth'],
        seg['io2io']['logic_depth'],
        seg['io2reg']['logic_depth'],
        seg['reg2io']['pure_comb_depth'],
        seg['io2io']['pure_comb_depth'],
        seg['io2reg']['pure_comb_depth'],
        seg['reg2io']['top_cell_delay'] if seg['reg2io']['top_cell_delay'] is not None else 'NA',
        seg['io2io']['top_cell_delay'] if seg['io2io']['top_cell_delay'] is not None else 'NA',
        seg['io2reg']['top_cell_delay'] if seg['io2reg']['top_cell_delay'] is not None else 'NA',
        seg['reg2io']['top_net_delay'] if seg['reg2io']['top_net_delay'] is not None else 'NA',
        seg['io2io']['top_net_delay'] if seg['io2io']['top_net_delay'] is not None else 'NA',
        seg['io2reg']['top_net_delay'] if seg['io2reg']['top_net_delay'] is not None else 'NA',
        path_acc['max_fanout'],
        path_acc['max_cap'] if path_acc['max_cap'] is not None else 'NA',
        seg['reg2io']['top_cap'] if seg['reg2io']['top_cap'] is not None else 'NA',
        seg['io2io']['top_cap'] if seg['io2io']['top_cap'] is not None else 'NA',
        seg['io2reg']['top_cap'] if seg['io2reg']['top_cap'] is not None else 'NA',
        seg['reg2io']['max_fanout'] if seg['reg2io']['max_fanout'] is not None else 'NA',
        seg['io2io']['max_fanout'] if seg['io2io']['max_fanout'] is not None else 'NA',
        seg['io2reg']['max_fanout'] if seg['io2reg']['max_fanout'] is not None else 'NA'
    ]
    what_if_row = {
        'startpoint': path_acc['startpoint'],
        'endpoint': path_acc['endpoint'],
        'path_direction': direction,
        'output_port_hm': seg.get('output_port_hm'),
        'input_port_hm': seg.get('input_port_hm'),
        'data_required_time': path_acc.get('data_required_time'),
        'data_arrival_time': path_acc.get('data_arrival_time'),
        'slack': path_acc.get('slack'),
        'max_delay': what_if.get('max_delay'),
        'internal_original_delay': seg['io2io']['stage_plus_net_delay'],
        'internal_capped_delay': seg['io2io']['capped_total_delay'],
        'internal_post_removal': seg['io2io']['capped_after_bufinv_removal_delay'],
        'achievable_arrival': what_if.get('achievable_arrival'),
        'what_if_slack': what_if.get('what_if_slack'),
        'arrival_post_removal': what_if.get('arrival_post_removal'),
        'slack_post_removal': what_if.get('slack_post_removal'),
        'dominant': what_if.get('dominant'),
        'path_status': what_if.get('path_status'),
        'reg2io_original': seg['reg2io']['stage_plus_net_delay'],
        'io2io_original': seg['io2io']['stage_plus_net_delay'],
        'io2reg_original': seg['io2reg']['stage_plus_net_delay'],
        'reg2io_capped': seg['reg2io']['capped_total_delay'],
        'io2io_capped': seg['io2io']['capped_total_delay'],
        'io2reg_capped': seg['io2reg']['capped_total_delay'],
        'reg2io_post_removal': seg['reg2io']['capped_after_bufinv_removal_delay'],
        'io2io_post_removal': seg['io2io']['capped_after_bufinv_removal_delay'],
        'io2reg_post_removal': seg['io2reg']['capped_after_bufinv_removal_delay'],
        'seg_a_original': seg['reg2io']['stage_plus_net_delay'],
        'seg_b_original': seg['io2reg']['stage_plus_net_delay'],
        'seg_a_capped': seg['reg2io']['capped_total_delay'],
        'seg_b_capped': seg['io2reg']['capped_total_delay'],
        'seg_a_post_removal': seg['reg2io']['capped_after_bufinv_removal_delay'],
        'seg_b_post_removal': seg['io2reg']['capped_after_bufinv_removal_delay']
    }
    if max_delay is not None:
        sink.write_what_if_row(broad, what_if_row)

    sink.write_row(broad, row, start_cell=start_cell, end_cell=end_cell)


def parse_one_report(report_path, out_dir, analysis_type, ip_leaf_names, max_delay, logger):
    base = os.path.basename(report_path)
    out_name = '{0}_analysis.xlsx'.format(base)
    out_path = os.path.join(out_dir, out_name)

    logger.info('Processing report: %s', report_path)
    sink = XlsxSink(out_path, enable_what_if=(max_delay is not None))

    path_acc = new_path_acc()
    pending_stage = None
    in_point_table = False
    in_data_section = False
    point_cols = ['fanout', 'incr', 'path', 'other']

    need_clock_edge_value = False
    need_clock_net_value = False

    path_count = 0
    line_count = 0

    with open(report_path, 'r', errors='replace') as fin:
        for raw_line in fin:
            line_count += 1
            line = raw_line.rstrip('\n')

            m = _STARTPOINT_REGEX_.match(line)
            if m:
                path_acc = new_path_acc()
                path_acc['report_name'] = base
                pending_stage = None
                in_point_table = False
                in_data_section = False
                need_clock_edge_value = False
                need_clock_net_value = False
                path_acc['startpoint'] = m.group(1).strip()
                continue

            m = _ENDPOINT_REGEX_.match(line)
            if m:
                path_acc['endpoint'] = m.group(1).strip()
                continue

            m = _LAST_COMMON_PIN_REGEX_.match(line)
            if m:
                path_acc['last_common_pin'] = m.group(1).strip()
                continue

            m = _PATH_GROUP_REGEX_.match(line)
            if m:
                path_acc['path_group'] = m.group(1).strip()
                continue

            m = _PATH_TYPE_REGEX_.match(line)
            if m:
                path_acc['path_type'] = m.group(1).strip().lower()
                continue

            m = _CLOCK_EDGE_REGEX_.match(line)
            if m:
                clk_name = m.group(1).strip()
                rest = m.group(3).strip()
                path_acc['clock_names'].append(clk_name)
                nums = parse_numeric_tokens(rest)
                if nums:
                    val = safe_float(nums[0])
                    if val is not None:
                        path_acc['clock_edge_values'].append(val)
                        need_clock_edge_value = False
                    else:
                        need_clock_edge_value = True
                else:
                    need_clock_edge_value = True
                continue

            if need_clock_edge_value:
                nums = parse_numeric_tokens(line)
                if nums:
                    val = safe_float(nums[0])
                    if val is not None:
                        path_acc['clock_edge_values'].append(val)
                    need_clock_edge_value = False
                continue

            m = _CLOCK_NETWORK_DELAY_REGEX_.match(line)
            if m:
                rest = m.group(1).strip()
                nums = parse_numeric_tokens(rest)
                if nums:
                    val = safe_float(nums[0])
                    if val is not None:
                        path_acc['clock_net_values'].append(val)
                        need_clock_net_value = False
                    else:
                        need_clock_net_value = True
                else:
                    need_clock_net_value = True
                continue

            if need_clock_net_value:
                nums = parse_numeric_tokens(line)
                if nums:
                    val = safe_float(nums[0])
                    if val is not None:
                        path_acc['clock_net_values'].append(val)
                    need_clock_net_value = False
                continue

            if line.strip().startswith('clock source latency'):
                nums = parse_numeric_tokens(line)
                if nums:
                    # First numeric value is the incremental source latency term.
                    v = safe_float(nums[0])
                    if v is not None:
                        path_acc['clock_source_values'].append(v)
                continue

            if line.strip().startswith('clock ') and '(source latency)' in line:
                nums = parse_numeric_tokens(line)
                if nums:
                    v = safe_float(nums[0])
                    if v is not None:
                        path_acc['clock_source_values'].append(v)
                continue

            m = _CPPR_REGEX_.match(line)
            if m:
                v = safe_float(m.group(1))
                if v is not None:
                    path_acc['cppr'] = abs(v)
                continue

            m = _UNCERTAINTY_REGEX_.match(line)
            if m:
                v = safe_float(m.group(2))
                if v is not None:
                    path_acc['uncertainty'] = v
                continue

            m = _LIBRARY_TIME_REGEX_.match(line)
            if m:
                term = m.group(1).strip().lower()
                v = safe_float(m.group(2))
                if v is not None:
                    if analysis_type == 'setup' and term in ('setup', 'recovery'):
                        path_acc['lib_time'] = v
                    elif analysis_type == 'hold' and term in ('hold', 'removal'):
                        path_acc['lib_time'] = v
                    elif path_acc['lib_time'] is None:
                        path_acc['lib_time'] = v
                continue

            m = _PATH_MARGIN_REGEX_.match(line)
            if m:
                v = safe_float(m.group(1))
                if v is not None:
                    path_acc['path_margin'] = v
                continue

            if line.strip().startswith('data arrival time'):
                nums = parse_numeric_tokens(line)
                if nums and path_acc.get('data_arrival_time') is None:
                    path_acc['data_arrival_time'] = safe_float(nums[-1])
                if in_point_table:
                    finalize_stage(path_acc, pending_stage)
                    pending_stage = None
                    in_data_section = False
                continue

            if line.strip().startswith('data required time'):
                nums = parse_numeric_tokens(line)
                if nums:
                    path_acc['data_required_time'] = safe_float(nums[-1])
                if in_point_table:
                    finalize_stage(path_acc, pending_stage)
                    pending_stage = None
                continue

            if _POINT_HEADER_REGEX_.match(line):
                in_point_table = True
                in_data_section = True
                pending_stage = None
                point_cols = parse_point_columns(line)
                continue

            if in_point_table:
                sm = _STAGE_LINE_REGEX_.match(line)
                if sm and in_data_section:
                    finalize_stage(path_acc, pending_stage)

                    stage_name = sm.group(1).strip()
                    type_text = sm.group(2).strip()
                    rest = sm.group(3).strip()
                    stype = classify_stage(stage_name, type_text, ip_leaf_names)
                    inst = instance_from_stage(stage_name)

                    pending_stage = {
                        'stage_name': stage_name,
                        'type_text': type_text,
                        'stype': stype,
                        'instance': inst,
                        'fanout': None,
                        'incr': None,
                        'transition': None,
                        'delta': None,
                        'cap': None,
                    }
                    if rest:
                        clean = strip_trailing_location(rest)
                        nums = parse_numeric_tokens(clean)
                        if nums:
                            if pending_stage.get('stype') == 'net':
                                if pending_stage.get('fanout') is None and len(nums) >= 1:
                                    pending_stage['fanout'] = safe_float(nums[0])
                                if pending_stage.get('cap') is None and len(nums) >= 2:
                                    pending_stage['cap'] = safe_float(nums[1])
                            else:
                                parsed = parse_stage_metrics_from_nums(nums)
                                if pending_stage.get('incr') is None:
                                    pending_stage['incr'] = parsed.get('incr')
                                if pending_stage.get('transition') is None:
                                    pending_stage['transition'] = parsed.get('transition')
                                if pending_stage.get('delta') is None:
                                    pending_stage['delta'] = parsed.get('delta')
                    continue

                if pending_stage is not None and in_data_section:
                    clean = strip_trailing_location(line)
                    nums = parse_numeric_tokens(clean)
                    if nums:
                        if pending_stage.get('stype') == 'net':
                            if pending_stage.get('fanout') is None and len(nums) >= 1:
                                pending_stage['fanout'] = safe_float(nums[0])
                            if pending_stage.get('cap') is None and len(nums) >= 2:
                                pending_stage['cap'] = safe_float(nums[1])
                        else:
                            parsed = parse_stage_metrics_from_nums(nums)
                            if pending_stage.get('incr') is None:
                                pending_stage['incr'] = parsed.get('incr')
                            if pending_stage.get('transition') is None:
                                pending_stage['transition'] = parsed.get('transition')
                            if pending_stage.get('delta') is None:
                                pending_stage['delta'] = parsed.get('delta')
                    continue

            m = _SLACK_REGEX_.match(line)
            if m:
                v = safe_float(m.group(1))
                if v is not None:
                    path_acc['slack'] = v

                if len(path_acc['clock_names']) >= 1:
                    path_acc['launch_clock'] = path_acc['clock_names'][0]
                if len(path_acc['clock_names']) >= 2:
                    path_acc['capture_clock'] = path_acc['clock_names'][1]

                if len(path_acc['clock_edge_values']) >= 1:
                    path_acc['launch_edge'] = path_acc['clock_edge_values'][0]
                if len(path_acc['clock_edge_values']) >= 2:
                    path_acc['capture_edge'] = path_acc['clock_edge_values'][1]

                if len(path_acc['clock_source_values']) >= 1:
                    path_acc['launch_source_delay'] = path_acc['clock_source_values'][0]
                if len(path_acc['clock_source_values']) >= 2:
                    path_acc['capture_source_delay'] = path_acc['clock_source_values'][1]

                if len(path_acc['clock_net_values']) >= 1:
                    path_acc['launch_net_delay'] = path_acc['clock_net_values'][0]
                if len(path_acc['clock_net_values']) >= 2:
                    path_acc['capture_net_delay'] = path_acc['clock_net_values'][1]

                want_path = True
                ptype = path_acc['path_type']
                if analysis_type == 'setup' and ptype == 'min':
                    want_path = False
                if analysis_type == 'hold' and ptype == 'max':
                    want_path = False

                if want_path:
                    write_path_row(path_acc, sink, ip_leaf_names, max_delay, analysis_type)
                    path_count += 1

                    if path_count % 10000 == 0:
                        logger.info('Parsed %d paths from %s (line %d)', path_count, base, line_count)

                path_acc = new_path_acc()
                pending_stage = None
                in_point_table = False
                in_data_section = False
                need_clock_edge_value = False
                need_clock_net_value = False

    sink.close()
    logger.info(IM._LOGMSG_COMPLETED_REPORT_, base, path_count, out_path)


def make_logger(verbose):
    logger = logging.getLogger('pt_timing_analyzer')
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    fmt = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    handler.setFormatter(fmt)
    logger.handlers = [handler]
    logger.propagate = False
    return logger


def parse_args():
    parser = argparse.ArgumentParser(description=IM._ARGPARSE_ANALYZER_DESC_)
    parser.add_argument('-i', '--input', required=True, help=IM._ARGHELP_INPUT_)
    parser.add_argument('-o', '--output-dir', required=True, help=IM._ARGHELP_OUTPUT_DIR_)
    parser.add_argument('-a', '--analysis-type', required=True, choices=['setup', 'hold'], help=IM._ARGHELP_ANALYSIS_TYPE_)
    parser.add_argument('-md', '--max-delay', type=float, default=None, help=IM._ARGHELP_MAX_DELAY_)
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose logging')
    return parser.parse_args()


def main():
    args = parse_args()
    logger = make_logger(args.verbose)

    in_path = os.path.abspath(args.input)
    out_dir = os.path.abspath(args.output_dir)

    if not os.path.exists(in_path):
        logger.error(IM._LOGMSG_INPUT_NOT_EXIST_, in_path)
        return 2

    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)

    if args.max_delay is not None and args.max_delay < 0.0:
        logger.error(IM._LOGMSG_MAX_DELAY_INVALID_)
        return 2

    logger.info(IM._LOGMSG_BUILDING_IP_SET_, IP_SCAN_ROOT)
    ip_leaf_names = list_ip_leaf_names(IP_SCAN_ROOT)
    logger.info('IP leaf-name set size: %d', len(ip_leaf_names))

    reports = list(iter_report_files(in_path))
    if not reports:
        logger.error('No report files found under input: %s', in_path)
        return 2

    logger.info('Found %d report file(s)', len(reports))
    for report in reports:
        parse_one_report(report, out_dir, args.analysis_type, ip_leaf_names, args.max_delay, logger)

    logger.info('All reports processed successfully.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
