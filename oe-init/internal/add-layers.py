#! /usr/bin/env python3

import subprocess, sys, re, argparse, os, shutil, json

bblayers_file = None
bblayers_backup = None

def main():

	global bblayers_file
	global bblayers_backup

	parser = argparse.ArgumentParser(description='Manage the build tree')

	parser.add_argument('--layers', help='JSON List of layers to add to build',
		default='default')

	args = parser.parse_args()

	if args.layers is None:
		print_info("No layers to add, exiting")
		exit(0)

	if not shutil.which("bitbake-layers"):
		print_error("missing 'bitbake-layers' command, please ensure "
			"bitbake environment is sourced")
		exit(1)

	try:
		layers = json.loads(args.layers)
	except:
		print_error("Failed to load json layers list")
		exit(1)

	added_layers = []
	layers = list(set(layers))
	layer_count = len(layers)

	cmd = ["bitbake", "-e"]
	output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)

	for line in output.decode("utf-8").splitlines():
		if "bblayers.conf" in line:
			bblayers_file = line.split()[1]
			break

	bblayers_backup = bblayers_file + ".autobk"

	print_info("Adding layers, this may take a while...")

	while len(added_layers) != layer_count:

		added_layers_count = len(added_layers)

		for layer in layers[:]:
			if add_layer(layer):
				added_layers.append(layer)
				layers.remove(layer)

		if len(added_layers) == added_layers_count:
			print_error("Some layers could not be added, check dependant layers "
				"exist, and for circular dependancies")
			print_info("Layers added: {}".format(added_layers))
			print_info("Layers failed: {}".format(layers))
			exit(1)

	print_info("All layers sucessfully added")


def add_layer(layer):

	global bblayers_file
	global bblayers_backup

	try:
		shutil.copyfile(bblayers_file, bblayers_backup)

		cmd = ["bitbake-layers", "add-layer",  layer]
		subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

		cmd = ["bitbake", "-p"]
		subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

		print_info("Added layer {} sucessfully".format(layer))

	except subprocess.CalledProcessError as e:
		shutil.copyfile(bblayers_backup, bblayers_file)
		return False

	return True

def print_info(text):

	print('\x1b[0;32m' + 'INFO: ' + '\x1b[0m' + text)

def print_error(text):

	print('\x1b[0;31m' + 'ERROR: ' + '\x1b[0m' + text)

if __name__ == '__main__':
	main()
