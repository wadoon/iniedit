#!/usr/bin/env python

import re, cmd, time

def read_ini_file( file ):
	re_pair = re.compile('\w*=\w*')
	re_section = re.compile('\[.*\]')
    
	product = IniFile();
	last_section = None

	for line in file.readlines():
		line = line.strip()

		if   line == '': continue
		elif line[0] ==';' or line[0] == '#':
			#print 'c :: ' , line
			product.addComment(line)
		elif re_section.match(line):  
			match = re_section.match(line)
			( comment , last_section)  = ( line[match.end()+1:] , match.group().strip('[]') )
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

def write_ini_file( file, ini, close=False, lb_sec_ch = True, lb_com_ch = True, indent=None):
		lastElement = None
		for ele in ini.elements:
				currElement = ele.__class__
				#print currElement
				if (currElement == Section and lb_sec_ch ) or 												\
				   (currElement == Comment and lastElement != Comment): file.write('\n')
				file.write( str(ele)  + '\n' )				

				if currElement == Section:
					for pair in ele.pairs:
						file.write(indent)
						file.write( str(pair)  + '\n')

				if lastElement == Comment and lb_com_ch and currElement != lastElement:
					file.write('\n'); 				
				lastElement = currElement

		if close:
			close(file)


class IniFile:
	"""This class represent a INI-File. You can add or remove Section and additionaly comments!
This systems tries to leave the INI-File in the format before the manupulation!"""
	def __init__(self):		
		self.elements = []
		
	def addElement(self, element, section = None):
		#print element.__class__
		if element.__class__ in [Pair, Comment, Section]:
			if section is None:
				self.elements.append( element );
			else:
				section = self[section]
				if section is None:
					self.addSection(section)
					self.addElement(element, section)
				else:
					section.addElement(element)
		
	def addComment(self, comment):
		self.addElement( Comment( comment ) );
	
	def addSection(self, name):
		self.addElement( Section( name ) );
	
	def addKey(self, section, key, value, comment = None):
		if section is None:
			self.elements.append(Pair(key, value, comment));
			return
	
		section = self[section]
		if section is None:
			self.addSection(section)
			self.addKey(section, key, value)
		else:
			section.add(key, value)
	
	def __getitem__(self, key):
		for sec in self.elements:
			if isinstance(sec, Section):
				if sec.name == key:
					return sec;
			elif isinstance(sec, Pair):
				if sec.key == key:
					return sec;
		return None;

	def __delitem__(self,key):
#		print "delete key ", key
		for sec in self.elements:
			if isinstance(sec, Section):
				if sec.name == key:
					self.elements.remove(sec)
			if  isinstance(sec, Pair):
				if sec.key == key:
					self.elements.remove(sec)

	def __getattr__(self, name):
#		print name
		for p in self.elements:
			if isinstance(p, Pair):
				if p.key  == name:
					return p;	
			
class Section:
	def __init__(self, section_name, comment = None ):
		self.name = section_name
		self.comment = Comment( comment	)

		self.pairs = []

	def addElement(self, element):
		self.pairs.append(element)

	def add(self, key, value):
		self.pairs.append( Pair(key, value) )
	
	def __str__(self):		
		if self.name is None:
			return ""
		else:
			return '[' + self.name +']' + str(self.comment)

	def	__getitem__(self, key):
		for pair in self.pairs:
			if pair.key == key:
				return pair	
		return None

	def __delitem__(self, key):
		for pair in self.pairs:
				if pair.key == key:
					self.pairs.remove(pair)

	def __setitem__(self, key, value):
			if self[key] is None:
				self.add(key,value)
			else:
				self[key].value = value
	
class Pair:
	def __init__(self, key, value = None, comment = None):
		self.comment = Comment( comment )
		self.key = key
		self.value = value

	def __str__(self):
		return self.key + '=' + self.value;			

class Comment:
	def __init__(self, comment):
		self.comment = comment

	def __str__(self):
		if not bool(self.comment): 
			return ''
		elif self.comment[0] == ';':
			return self.comment
		else:
			return ';' + self.comment



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
		
def setValue(product, key , value , section = None):
	if section is None:
		k = product[key]
	else:
		k = 
		if k is None:
			product.addKey(

if __name__ == '__main__':
	from optparse import OptionParser
	import sys

	parser = OptionParser("%prog [Commands] [FILE]")
	parser.add_option("", "--list", dest="list",help="sets what you want to dump")
	parser.add_option("", "--section", dest="section", default=None, help="sets the section you want to manupulate")
	parser.add_option("-i", "--interactive", dest="interactive", default=False, action="store_true" ,
					  help="open the interactive command line")

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
	
	if printOut:
		write_ini_file(sys.stdout, product, indent='  ')

