#! /usr/bin/env python3

import subprocess, sys, re, argparse, os, shutil, json

def main():

	parser = argparse.ArgumentParser(description='Generate an OE setup script')

	parser.add_argument('--base-path', help='Path to base working directory', default=None)
	parser.add_argument('--layers-path', help='Path to OE layers directory', default='openembedded')
	parser.add_argument('--machine', help='Machine name', default='select')
	parser.add_argument('--distro', help='Distro name', default='select')
	parser.add_argument('--build-dir', help='Build dir location', default='default')
	parser.add_argument('--dl-dir', help='Download directory location', default='default')
	parser.add_argument('--ss-dir', help='Shared state directory location', default='default')
	parser.add_argument('--pers-dir', help='Shared persistent cache directory location', default='default')

	args = parser.parse_args()

	if not args.base_path:
		print_error("Please provide a base directory for initialising builds")
		exit(1)

	root_path = args.base_path
	root_path = os.path.abspath(root_path)

	layers_path = args.layers_path
	layers_path = os.path.abspath(layers_path)

	selected_machine = None

	machines = parse_machines(layers_path)
	distros = parse_distro(layers_path)

	if args.machine != "select":
		for (layer, machine) in machines:
			if machine == args.machine:
				selected_machine = (layer, machine)
				break

		if not selected_machine:
			print_error("specified machine not found in any layers")
			exit(1)

	else:

		selected_machine = whiptail_menu("Select Machine", machines)

		if not selected_machine:
			print_error("failed to select machine, please try again or specify "					"manually with --machine")
			exit(1)

	print_info("Selected machine: " + selected_machine[1])

	if args.distro != "select":
		for (layer, distro) in distros:
			if distro == args.distro:
				selected_distro = (layer, distro)
				break

		if not selected_distro:
			print_error("specified distro not found in any layers")
			exit(1)

	else:

		selected_distro = whiptail_menu("Select Distro", distros)

		if not selected_distro:
			print_error("failed to select distro, please try again or specify "					"manually with --distro")
			exit(1)

	print_info("Selected distro: " + selected_distro[1])

	if args.build_dir == "default":
		build_dir = "build-{}".format(selected_machine[1])
		build_dir = os.path.join(root_path, build_dir)
	else:
		build_dir = args.build_dir

	build_dir = os.path.abspath(build_dir)
	print_info("Selected build dir: " + build_dir)

	if args.dl_dir == "default":
		dl_dir = os.path.join(root_path, "downloads")
	else:
		dl_dir = args.dl_dir

	dl_dir = os.path.abspath(dl_dir)
	print_info("Selected download dir: " + dl_dir)

	if args.ss_dir == "default":
		ss_dir = os.path.join(root_path, "sstate")
	else:
		ss_dir = args.ss_dir

	ss_dir = os.path.abspath(ss_dir)
	print_info("Selected shared state dir: " + ss_dir)

	if args.pers_dir == "default":
		pers_dir = os.path.join(root_path, "cache")
	else:
		pers_dir = args.pers_dir

	pers_dir = os.path.abspath(pers_dir)
	print_info("Selected persistence dir: " + pers_dir)

	bblayer_paths = generate_bblayers(layers_path, selected_machine[0])
	bblayer_paths += generate_bblayers(layers_path, selected_distro[0])
	bblayer_paths.append(os.path.join(layers_path, selected_machine[0]))
	bblayer_paths.append(os.path.join(layers_path, selected_distro[0]))

	try:
		os.makedirs(build_dir)
	except:
		print_error("Build directory already exists, please remove if restarting build")
		print_error("or specify an alternative directory with --build-dir")
		print_error(build_dir)
		exit(1)

	if not os.path.isdir(root_path):

		try:
			os.makedirs(root_path)
		except:
			print_error("base-path " + root_path + " is not writeable")
			exit(1)

	source_file = open(root_path + "/.setup_build", "w")

	source_file.write("MACHINE={}\n".format(selected_machine[1]))
	source_file.write("DISTRO={}\n".format(selected_distro[1]))
	source_file.write("BUILDDIR={}\n".format(build_dir))
	source_file.write("DL_DIR={}\n".format(dl_dir))
	source_file.write("SSTATE_DIR={}\n".format(ss_dir))
	source_file.write("PERSISTENT_DIR={}\n".format(pers_dir))
	source_file.write("BBLAYERS='{}'\n".format(json.dumps(bblayer_paths)))
	source_file.write("EXEC='source {0}/oe-core.git/oe-init-build-env {1} {0}/bitbake.git'\n".format(layers_path, build_dir))
	source_file.write("source {0}/oe-core.git/oe-init-build-env {1} {0}/bitbake.git\n".format(layers_path, build_dir))

	source_file.close()

	print_info("Generated setup script")

def whiptail_menu(title, menu_table):

	if not shutil.which("whiptail"):
		print_error("missing 'whiptail' gui command, please manually specify a machine "
			"with --machine")
		exit(1)

	cmd = ["whiptail"]
	cmd.extend(["--title", "'{}'".format(title)])

	# Output to stderr to catch result
	cmd.extend(["--output-fd", "2"])

	cmd.extend(["--menu", "", "0", "0", "20"])

	for menu_item in menu_table:
		cmd.append("{}".format(menu_item[1]))
		cmd.append("{}".format(menu_item[0]))

	p = subprocess.Popen(cmd, stderr=subprocess.PIPE)
	(out, err) = p.communicate()

	if (len(err) == 0):
		return None
	else:
		for item in menu_table:
			if item[1] == err.decode("utf-8"):
				return item

	return None

def generate_bblayers(layers_path, layer_folder):

	avail_layers = []

	for directory in find_dirs(layers_path, "conf"):
		for root, dirs, files in os.walk(directory):

			if "lib/layerindexlib/tests/testdata" in root:
				continue

			for filename in files:
				if filename == "layer.conf":
					layer_name = find_var_file(os.path.join(root, filename), "BBFILE_COLLECTIONS")
					avail_layers.append((layer_name[0], os.path.abspath(os.path.join(root, "../"))))

	deps = find_layer_deps(layers_path, layer_folder)
	bblayers = []

	if deps:

		while True:
			count = len(deps)
			for dep in deps:
				for layer in avail_layers:
					if layer[0] == dep:
						new_deps = find_layer_deps(layers_path, layer[1])
						if new_deps:
							deps.extend(new_deps)

			deps = list(set(deps))

			if count == len(deps):
				break

		for layer in avail_layers:
			if layer[0] in deps:
				bblayers.insert(0, layer[1])

	return bblayers

def find_layer_deps(layers_path, layer_folder):

	layer_conf = os.path.join(layers_path, layer_folder, "conf/layer.conf")
	layer_deps = find_var_file(layer_conf, "LAYERDEPENDS")

	return layer_deps

def search_layer_conf_dir(layer_root, search):

	found_list = []

	num_dirs = len(layer_root.split("/"))

	for directory in find_dirs(layer_root, search):
		for root, dirs, files in os.walk(directory):
			for filename in files:
				if re.search(".conf", filename):
					conf_dir_level = 0
					split_root = root.split("/")

					for dir_name in split_root:
						if dir_name == "conf":
							break
						conf_dir_level += 1

					final_path = "/".join(split_root[num_dirs:conf_dir_level])
					found_list.append((final_path, filename[:-5]))

	found_list.sort()
	return found_list

def parse_machines(path):

	return search_layer_conf_dir(path, "machine")

def parse_distro(path):

	return search_layer_conf_dir(path, "distro")

def find_var_file(file_path, var):

	split_string = []
	layer_conf = open(file_path, "r")
	found = 0
	multiline = ""

	for line in layer_conf:

		line = line.strip()

		if line.rstrip()[-1:] == "\\":
			multiline += line.rstrip()[:-1]
			continue

		if multiline != "":
			line = multiline + line

		if var in line:
			found = 1
			split_string.extend(re.findall(r'"([^"]*)"', line)[0].split(" "))

		multiline = ""

	layer_conf.close()

	if found == 0:
		return None

	return split_string

def find_dirs(path, name):

	for root, dirs, files in os.walk(path):
		for directory in dirs:
			if directory == name:
				yield os.path.join(root, directory)

def print_info(text):

	print('\x1b[0;32m' + 'INFO: ' + '\x1b[0m' + text)

def print_error(text):

	print('\x1b[0;31m' + 'ERROR: ' + '\x1b[0m' + text)

if __name__ == '__main__':
	main()
