#!/usr/bin/python3

import xml.etree.ElementTree as etree
import subprocess, sys, re, argparse

parser = argparse.ArgumentParser(description='Manage the build tree')

parser.add_argument('--init', help='Setup git tree remotes to match repo manifest', action='store_true')
parser.add_argument('--checkout-default', help='Checkout default branches to match repo manifest', action='store_true')

args = parser.parse_args()

tree = etree.parse('.repo/manifests/default.xml')

root = tree.getroot()

defaults = root.find('default')
default_remote = defaults.attrib['remote']

projects = root.findall('project')

for project in projects:

	path = project.attrib['path']
	name = project.attrib['name']

	try:
		revision = project.attrib['revision']

		if len(revision) == 40:
			revision = project.attrib['branch']

	except:
		revision = default_revision

	try:
		remote = project.attrib['remote']
	except:
		remote = default_remote

	try:
		if args.init:
			subargs = ['git', 'checkout', '--track', '-b', revision, "{}/{}".format(remote, revision)]
			output = subprocess.check_output(
				subargs,
				cwd=path,
				stderr=subprocess.STDOUT)

		if args.checkout_default:
			subargs = ['git', 'checkout', revision]
			output = subprocess.check_output(
				subargs,
				cwd=path,
				stderr=subprocess.STDOUT)

		sys.stdout.buffer.write(output)

	except subprocess.CalledProcessError as e:

		sys.stdout.buffer.write(e.output)
		print(e.cmd)

