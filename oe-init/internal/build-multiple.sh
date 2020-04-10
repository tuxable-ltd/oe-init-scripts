#! /bin/bash -e

machines=$1
images=$2
distros=$3

if [ ! -e scripts/init-new-build ]
then
    echo "Please execute script from base repo directory"
    exit 1
fi

base=$(pwd)

for distro in ${distros//,/ }
do
	for machine in ${machines//,/ }
	do

	    build_dir=build-multi_${distro}_${machine}

	    scripts/init-new-build --machine $machine --distro $distro --build-dir $build_dir
	    . $build_dir/source_build

	    for image in ${images//,/ }
	    do
		bitbake $image
	    done

	    cd $base

	done
done

echo "Finished builds successfully"
