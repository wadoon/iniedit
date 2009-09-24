#!/usr/bin/env python

import re, cmd, time, sys

def stdwrapper(file):
	def __init__(self, write=sys.stdout, read=sys.stdin):
		self.closed=False
		self.encoding=sys.stdout.encoding
		self.errors=sys.stdout.errors
		self.fileno=sys.stdout.fileno
		self.mode="rw"
		self.name=None
		self.newlines=sys.stdout.newlines
		
		self.write= write
		self.read = read
		
		print "stdwrapper"
		
	def __enter__(self): 	return self
	def __exit__(self): 	pass 
	def __format__(self): 	pass
	def close(self): 	pass 
	
	def flush(self):
		self.write.flush()
		self.read.flush()
	
	def isatty(self):            return self.read.isatty() 
	def next(self):   	     return self.readline()
	def read(self,*args):        return self.read.read(*args)
	def readinto(self,*args):    return self.read.readinto(*args)
	def readline(self, *args):   return self.read.readline(*args) 
	def readlines(self, *args):  return self.read.readlines(*args) 
	def seek(self, *args): pass
	def tell(self): return 0 
	def truncate(self): pass
	def write(self, *args):      return self.write.write(*args) 
	def writelines(self, *args): return self.write.writelines(*args)
	def xreadlines(self, *args): return self.read.xreadlines(*args)


def open(filename, mode="r", buffering=0):
	if isinstance(filename, file):
		if filename == "-": return stdwrapper(filename,filename)
		else:   	return filename
	
	else:		    return __builtins__.open(filename, mode, buffering)

def read_ini_file( filename ):
	"""reads the stream from the given filename and returns an IniFile object"""
	with open(filename, 'r') as file:
		re_pair = re.compile('\w*\s*=\s*\w*')
		re_section = re.compile('\[.*\]')
	
		product = IniFile();
		
		last_section = None
	
		for line in file.xreadlines():
			line = line.strip()
			if   line == '': continue             #skip empty lines
			elif line[0] ==';' or line[0] == '#':
				#print 'c :: ' , line
				product.addComment(line)
			elif re_section.match(line):  
				match = re_section.match(line)
				( comment , last_section)  = ( line[match.end()+1:] , match.group().strip('[] ') )
				product.addElement( Section( last_section , comment  ) )
				#print 's :: ' , last_section
			elif re_pair.match(line):
				#print 'p :: ' , line
				match = re_pair.match(line)
				assignment = match.group()
				pos = assignment.find('=')
				key = assignment[0:pos].strip()
				value = assignment[ pos+1 : ].strip()
				#print "add to ", last_section
				product.addElement(Pair(key,value, line[match.end() +1 :]),last_section)
			else:
				print "discard line: " + line
		return product

def write_ini_file( filename, ini, lb_sec_ch = True, lb_com_ch = True, indent=""):
		"""writes the given @ini@ file object to the @filename@	
		@lb_sec_ch@ leading new line at a section change
		@lb_com_ch@ True for splitting up comments
		@indent@ for an leading str by the pairs
		"""
		with open(filename, 'w') as file:
			lastElement = None
						
			for ele in ini.elements:
				if isinstance(ele, Pair): 
					file.write(str(ele))
					file.write("\n")

			
			for ele in ini.elements:
				currElement = ele.__class__
				#print currElement

				if currElement is Pair: continue

				#no space between childs and section header
				if (currElement is Section and lb_sec_ch )        or \
				   (currElement is Comment and lastElement != Comment): #do not split up lines
					file.write('\n')

				file.write( str(ele)  + '\n' )
	
				if currElement == Section:
					for pair in ele.pairs:
						file.write(indent)
						file.write( str(pair)  + '\n')
	
				if lastElement == Comment and lb_com_ch and currElement != lastElement:
					file.write('\n')
				lastElement = currElement	


class IniFile:
	"""This class represent a INI-File. You can add or remove Section and additionaly comments!
This systems tries to leave the INI-File in the format before the manupulation!"""
	def __init__(self):
		self.elements = []
		
	def addElement(self, element, section = None):
		"""adds a new @element@ object {Pair, Comment, Section} to this ini file. If section is None it will append in the global section"""

		if element.__class__ in [Pair, Comment, Section]:
			if section is None:
				self.elements.append( element );
			else:
				try:
					section = self[section]
					section.addElement(element)
				except KeyError, e:
					self.addSection(section)
					self.addElement(element, section)
		
	def addComment(self, comment):
		"""appends an Comment from the given @comment@"""
		self.addElement( Comment( comment ) );
	
	def addSection(self, name):
		"""appends a new Section from @name@"""
		self.addElement( Section( name ) );
	
	def addKey(self, section, key, value, comment = None):
		"""add a new Key to the @section@, and @key@=@value@ with the given trailing @comment@"""
		self.addElement( Pair(key, value, comment) , section );

			
	def __getitem__(self, key):
		for sec in self.elements:
			if isinstance(sec, Section) and sec.name == key:	
					return sec;
			elif isinstance(sec, Pair) and sec.key == key:
					return sec;
		raise KeyError("now Section or Pair with key %s was found" % key)

	def __delitem__(self,key):
		self.elements.remove( self[key] )


class Section:
	"""represents an Section within an Ini-File with all it's children"""
	def __init__(self, section_name, comment = None ):
		self.name = section_name
		self.comment = Comment( comment	)
		self.pairs = []

	def addElement(self, element):
		"""adds a Pair or a Comment"""		
		self.pairs.append(element)

	def add(self, key, value,comment=None):
		"""adds a new Pair with @key@=@value@"""
		self.pairs.append( Pair(key, value, comment) )
	
	def __str__(self):
		"""Section output for ini-file"""
		if self.name is None:
			return ""
		else:
			return '[' + self.name +']' + str(self.comment)

	def	__getitem__(self, key):
		""" gets the Pair with the @key@"""
		for pair in self.pairs:
			if pair.key == key:
				return pair	
		raise KeyError("not Pair with key equals '%s' was found" % key)

	def __delitem__(self, key):		
		self.pairs.remove(self[key])

	def __contains__(self, key):
		try: 
			self[key]
			return True
		except KeyError , e:
			return False

	def __setitem__(self, key, value):
		if key in self: self[key].value = value
		else:		self.add(key,value)
	
		
	
class Pair:
	"""key/value-pair"""
	def __init__(self, key, value = None, comment = None):
		self.comment = Comment( comment )
		self.key = key
		self.value = value

	def __str__(self):
		return self.key + '=' + self.value

class Comment:
	"""Represents a Comment"""
	def __init__(self, comment = None):
		self.comment = comment
	
	def __bool__(self): return bool(self.comment)

	def __str__(self):
		if not self.comment:   		   return ''
		elif self.comment.startswith(";"): return       self.comment
		else:                              return ';' + self.comment



class IniCmd(cmd.Cmd):
	def __init__(self, product): 
		cmd.Cmd.__init__(self, '') 
		self.product = product
		self.prompt = ">>> "

	def parse(self, string):
		posCol = string.find(':')
		if posCol >= 0:
			section = string[0: posCol ].strip()
			if section == ':' :
				section = None
			offset = posCol + 1
		else:
			section = None
			offset = 0
		
		posEq = string.find('=')
		key = string[offset:None if posEq < 0 else posEq].strip()
		
		if posEq >= 0:
			value = string[posEq+1:].strip()
		else:
			value = None
			
		print section, '|', key , '|', value
		return (section, key, value)

 	def do_set(self, prm): 
		(section , key, value) = self.parse(prm)
		getValue(self.product , key , section).value = value
		
	def help_set(self): 
		print """Sets the value of a key.
Usage: section:key=value"""
		
	def do_ren(self, prm):
		(section , key, value) = self.parse( prm )
		
		if value is not None:				
			if key is None:
				renSection(self.product, section, key)
			else:
				renPair(self.product, section, key ,value)
		else:
			print "Error! Value is None."
		
		
	def help_ren(self):
		return """rename a section or a key
Usage: ren section:=value or section:key=value or key=value"""

	def do_del(self, prm): 
		(section , key, value) = self.parse( prm )	
		if section is None:
				delSection(self.product, key)
		elif key is None:
				delSection(self.product, section)
		else:		
				delPair(self.product, section, key)

	def help_del(self): 
		print """delete a section or a key
Usage del section: or section:key or key"""

	def do_get(self, prm):
		(section , key, value) = self.parse( prm )
		if key is not None:
			print getValue(self.product, key, section).value
		else:
			print "Error, Key has to set!"
		
	def help_get(self):
		return """get the value from a key. 
Usage: get section:key or key"""; 

	def do_list(self, prm):
		if len(prm) == 0:
			write_ini_file(sys.stdout, self.product, indent='  ')
		else:
			print self.product[prm]
			for e in self.product[prm].pairs:
				print '  ', str(e)
		
	def help_list(self):
		pass

	def do_exit(self, prm): 
		return True
		
	def help_exit(self):
		return """close the session"""
		


def setPair(inifile , section, key , value):
#	print "[%s] %s=%s" % ( section , key , value)
	inifile[section][key] = value

def delPair(inifile, section, key):
	del inifile[section][key]

def delSection(inifile, section):
	del inifile[section]

def renSection(inifile, section, new_name):
	inifile[section].name = new_name
	
def renPair(product, section, key ,value):
	if section is not None:
		product[section][key].key = value
	else:
		getValue(product, key).key = value

def getValue(product , key , section = None):
	if section is None:
	#	print eval( "product.%s" % key ).value
		return  product[key]
	else:
		return product[section][key].value
		
#TODO ------------------------ something is wrong here
#def setValue(product, key , value , section = None):
#	if section is None:
#		k = product[key]
#	else:
#		k = #
#		if k is None:#
#			product.addKey(

if __name__ == '__main__':
	from optparse import OptionParser
	import sys

	parser = OptionParser("%prog [Commands] [FILE]")
	parser.add_option("", "--list", dest="list",help="sets what you want to dump")
	parser.add_option("", "--section", dest="section", default=None, help="sets the section you want to manupulate")
	parser.add_option("-i", "--interactive", dest="interactive", default=False, action="store_true" ,
					  help="open the interactive command line")

	parser.add_option("-o", "--output" , metavar="filename" , dest="output", default="-", help="filename for output the file")	

	parser.add_option("", "--set-pair", metavar="\"KEY=VALUE\"", dest="setpair", default=None,
				help="gives the key and the value you want to add/set! (e.g. key=value)")

	parser.add_option("", "--del-section", metavar="SECTION", dest="delsection", default=None,
				help="if set you can delete whole section")

	parser.add_option("", "--del-pair", metavar="KEY" ,dest="delpair", default=None,
				help="if set you can delete the key in the given --section")

	parser.add_option("", "--ren-section", metavar="NEW_SECTION" ,dest="rensection", default=None,
				help="specify the section with --section")

	parser.add_option("", "--ren-key", metavar="\"KEY=NEW_KEY\"" ,dest="renkey", default=None,
				help="specify the section with --section")

	parser.add_option("", "--get" , metavar="KEY" , dest="get", default=None, help="gets the key from the file")
	
	
	(options, args) = parser.parse_args()

#	print "I take %s" % args[0]

	read_in = sys.stdin if len(args) == 0 else open(args[0])
	
	product = read_ini_file(read_in)
	
	printOut = True
	
	if not options.interactive:
		if options.setpair is not None:
			pos = options.setpair.find('=')
			(key,value) = ( options.setpair[0:pos] , options.setpair[pos+1:] )
			section = options.section
			setPair(product, section, key ,value)
		elif options.delsection is not None:
			section = options.delsection
			delSection(product, section)
		elif options.delpair is not None:
			key = options.delpair
			section = options.section
			delPair(product, section, key)
		elif options.rensection is not None:
			to = options.rensection
			section = options.section
			renSection(product, section, to)			
		elif options.renkey is not None:
			pos = options.renkey.find('=')
			(key,value) = ( options.renkey[0:pos] , options.renkey[pos+1:] )
			section = options.section
			renPair(product, section, key ,value)
		elif options.get is not None:
			key = options.get
			section = options.section
			getValue(product, key, section)
			printOut=False
	else:
		IniCmd(product).cmdloop()
	
	if printOut: write_ini_file(opts.output , product, indent='  ')