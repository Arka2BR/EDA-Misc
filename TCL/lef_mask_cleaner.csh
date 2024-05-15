#! /bin/csh -f
foreach DIR ( an bn cn dn )
        cd $DIR
        sed -i 's/core2h \;/core ;/' *.lef 
        sed -i 's/STARTVARIANT 2 /STARTVARIANT 1 /' *.lef
        sed -i 's/ MASK 3 / /' *.lef
        sed -i 's/ MASK 2 / /' *.lef
        sed -i 's/ MASK 1 / /' *.lef
	sed -i 's/ FIXEDMASK ;/ /' *.lef
        cd ../
end
