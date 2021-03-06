#!/usr/bin/python
# -*- coding: utf-8 -*-

from vhdl import *
import sys, os

"""
vParser
=======

.. moduleauthor:: Jordi Masip <jordi@masip.cat>
"""

def read_file(filename):
	if not os.path.isfile(filename):
		print "error: l'arxiu '%s' no existeix" % filename
		sys.exit(1)

	try:
		with open(filename, "r") as f:
			content = f.read()
		return content
	
	except Exception as e:
		print "error: no hem pogut llegir l'arxiu '%s'" % filename
		sys.exit(1)

def write_file(filename, content):
	with open(filename, "w") as f:
		f.write(content)

def getBetween(s, pref, suf):
	try:
		start = 0 if pref == "" else s.index(pref)
		end = len(s) if suf == "" else s[start:].index(suf)
		return (s[start + len(pref):start+end], end)
	except Exception:
		return ("", -1)

def getLibs(vhdl_file):
	libs = {}
	if "library" not in vhdl_file:
		return []
	
	last_pos = 0
	
	while True:
		value = getBetween(vhdl_file[last_pos:], "library", ";")

		ignore_line = False

		for i in range(last_pos, value[1] + len(value[0]))[::-1]:
			if vhdl_file[i] == '\n':
				break

			if vhdl_file[i] == '-' and vhdl_file[i-1] == '-':
				ignore_line = True
				break
	
		last_pos += value[1]

		if value == ("", -1):
			break
		
		lib_name = value[0].strip().lower()
	
		if lib_name in libs:
			break

		if not ignore_line:
			libs[lib_name] = Library(lib_name)
	last_pos = 0
	
	while True:
		value = getBetween(vhdl_file[last_pos:], "use", ";")

		ignore_line = False

		for i in range(last_pos, value[1] + len(value[0]))[::-1]:
			if vhdl_file[i] == '\n':
				break

			if vhdl_file[i] == '-' and vhdl_file[i-1] == '-':
				ignore_line = True
				break

		last_pos += value[1]
	
		if value == ("", -1):
			break
	
		use_statment = value[0].strip().lower().split(".")
		lib, package = use_statment[0], ".".join(use_statment[1:])
	
		if lib in libs.keys():
			if not ignore_line:
				libs[lib].addPackage(package)
		else:
			print "error: s'està utilitzant la llibreria '%s' al paquet '%s.%s' sense haver-la afegit" % (lib, lib, package)
			break
	
	return libs.values()

def getEntities(vhdl_file):
	entities = []
	last_pos = 0
	
	while True:
		value = getBetween(vhdl_file[last_pos:], "entity", "is")
		entity = Entity(value[0].strip())
		
		if value == ("", -1) or entity in entities:
			break
		
		last_pos += value[1]
		between_entity = getBetween(vhdl_file, entity.getName() + " is", "end")[0].strip()
		port = ""
		bracket_counter = 0
		isCounting, isPortFound, isValidPort = False, False, False
		
		for i in range(len(between_entity)):
			if between_entity[i:i+4] == "port":
				isCounting = True
				isPortFound = True
			if isCounting:
				port += between_entity[i]
				if between_entity[i] == "(":
					bracket_counter += 1
				elif between_entity[i] == ")":
					bracket_counter -= 1
				elif between_entity[i] == ";" and bracket_counter == 0:
					isPortFound = True
					isValidPort = True
					break
		else:
			isValidPort = False

		if isValidPort:
			entity.setPortList(PortList(port))
		elif isPortFound:
			print "error: no es pot llegir el port definit a l'entitat '%s'" % entity.getName()
	
		entities += [entity]
	
	return entities

def getArchitectureOfEntity(vhdl_file, entity):
	last_pos = 0
	
	while True:
		value = getBetween(vhdl_file[last_pos:], "architecture", "begin")
		last_pos += value[1]
		arch_name = getBetween(value[0], "", " of")[0].strip()
		ent_name = getBetween(value[0], "of ", "is")[0].strip()
	
		if arch_name == "" or ent_name == "":
			break
		if ent_name != entity.getName():
			continue
		
		arch = Architecture(arch_name, entity)
		signals = getBetween(value[0], "is", "")[0].strip()
		
		if signals != "":
			arch.setSignalList(SignalList(signals))
		
		return arch
	
	print "error: no s'ha trobat cap arquitectura de l'entitat '%s'" % entity.getName()
	sys.exit(1)