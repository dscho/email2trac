#!/usr/bin/python
# Copyright (C) 2002
#
# This file is part of the email2trac utils
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2, or (at your option) any
# later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA
#
"""
emailfilter.py -- Email tickets to Trac.

A simple MTA filter to create Trac tickets from inbound emails.

Copyright 2005, Daniel Lundin <daniel@edgewall.com>
Copyright 2005, Edgewall Software

Changed By: Bas van der Vlies <basv@sara.nl>
Date      : 13 September 2005
Descr.    : Added config file and command line options, spam level
            detection, reply address and mailto option. Unicode support

Changed By: Walter de Jong <walter@sara.nl>
Descr.    : multipart-message code and trac attachments


The scripts reads emails from stdin and inserts directly into a Trac database.
MIME headers are mapped as follows:

	* From:      => Reporter
	             => CC (Optional via reply_address option)
	* Subject:   => Summary
	* Body       => Description
	* Component  => Can be set to SPAM via spam_level option

How to use
----------
 * Create an config file:
	[DEFAULT]                        # REQUIRED
	project      : /data/trac/test   # REQUIRED
	debug        : 1                 # OPTIONAL, if set print some DEBUG info
	spam_level   : 4                 # OPTIONAL, if set check for SPAM mail 
	reply_address: 1                 # OPTIONAL, if set then fill in ticket CC field
        umask        : 022               # OPTIONAL, if set then use this umask for creation of the attachments
	mailto_link  : 1                 # OPTIONAL, if set then [mailto:<CC>] in description 
	trac_version : 0.8               # OPTIONAL, default is 0.9

	[jouvin]                         # OPTIONAL project declaration, if set both fields necessary
	project      : /data/trac/jouvin # use -p|--project jouvin.  
        
 * default config file is : /etc/email2trac.conf

 * Commandline opions:
                -h | --help
                -c <value> | --component=<value>
                -f <config file> | --file=<config file>
                -p <project name> | --project=<project name>

SVN Info:
        $Id: email2trac.py 1523 2005-11-01 09:27:51Z bas $
"""

import os
import sys
import string
import getopt
import stat
import time
import email
import re
import urllib
import unicodedata
import ConfigParser
from email import Header
from stat import *
import mimetypes

trac_default_version = 0.9

class TicketEmailParser(object):
	env = None
	comment = '> '
    
	def __init__(self, env, parameters, version):
		self.env = env

		# Database connection
		#
		self.db = None

		self.VERSION = version
		if self.VERSION > 0.8:
			self.new_ticket = ticket.Ticket
			self.get_config = self.env.config.get
		else:
			self.new_ticket = Ticket.Ticket
			self.get_config = self.env.get_config

		if parameters.has_key('umask'):
			os.umask(int(parameters['umask'], 8))

		if parameters.has_key('debug'):
			self.DEBUG = int(parameters['debug'])
		else:
			self.DEBUG = 0

		if parameters.has_key('reply_address'):
			self.CC = int(parameters['reply_address'])
		else:
			self.CC = 0

		if parameters.has_key('mailto_link'):
			self.MAILTO = int(parameters['mailto_link'])
		else:
			self.MAILTO = 0

		if parameters.has_key('spam_level'):
			self.SPAM_LEVEL = int(parameters['spam_level'])
		else:
			self.SPAM_LEVEL = 0

		if parameters.has_key('email_comment'):
			self.comment = str(parameters['email_comment'])

		if parameters.has_key('email_header'):
			self.EMAIL_HEADER = int(parameters['email_header'])
		else:
			self.EMAIL_HEADER = 0


	# X-Spam-Score: *** (3.255) BAYES_50,DNS_FROM_AHBL_RHSBL,HTML_
	# Note if Spam_level then '*' are included
	def spam(self, message):
		if message.has_key('X-Spam-Score'):
			spam_l = string.split(message['X-Spam-Score'])
			number = spam_l[0].count('*')

			if number >= self.SPAM_LEVEL:
				return number

		return 0

	def to_unicode(self, str):
		"""
		Email has 7 bit ASCII code, convert it to unicode with the charset
		that is encoded in 7-bit ASCII code and encode it as utf-8 so TRAC 
		understands it.
		"""
		results =  Header.decode_header(str)
		str = None
		for text,format in results:
			if format:
				try:
					temp = unicode(text, format)
				except UnicodeError:
					# This always works 
					#
					temp = unicode(text, 'iso-8859-15')
				temp =  temp.encode('utf-8')
			else:
				temp = string.strip(text)

			if str:
				str = '%s %s' %(str, temp)
			else:
				str = temp

		return str

	def debug_attachments(self, message):
		n = 0
		for part in message.walk():
			if part.get_content_maintype() == 'multipart':      # multipart/* is just a container
				print 'TD: multipart container'
				continue

			n = n + 1
			print 'TD: part%d: Content-Type: %s' % (n, part.get_content_type())
			print 'TD: part%d: filename: %s' % (n, part.get_filename())

			if part.is_multipart():
				print 'TD: this part is multipart'
				payload = part.get_payload(decode=1)
				print 'TD: payload:', payload
			else:
				print 'TD: this part is not multipart'

			part_file = '/var/tmp/part%d' % n
			print 'TD: writing part%d (%s)' % (n,part_file)
			fx = open(part_file, 'wb')
			text = part.get_payload(decode=1)
			if not text:
				text = '(None)'
			fx.write(text)
			fx.close()
			try:
				os.chmod(part_file,S_IRWXU|S_IRWXG|S_IRWXO)
			except OSError:
				pass

	def email_header_txt(self, m):
#		if not m['Subject']:
#			subject = '(geen subject)'
#		else:
#			subject = self.to_unicode(m['Subject'])
#
#		head = "'''Subject:''' %s [[BR]]" % subject
#		if m['From'] and len(m['From']) > 0:
#			head = "%s'''From:''' %s [[BR]]" % (head, m['From'])
#		if m['Date'] and len(m['Date']) > 0:
#			head = "%s'''Date:''' %s [[BR]]" %(head, m['Date'])

		str = ''
		if m['To'] and len(m['To']) > 0 and m['To'] != 'hic@sara.nl':
			str = "'''To:''' %s [[BR]]" %(m['To'])
		if m['Cc'] and len(m['Cc']) > 0:
			str = "%s'''Cc:''' %s [[BR]]" % (str, m['Cc'])

		return str

	def parse(self, fp):
		msg = email.message_from_file(fp)
		if not msg:
			return

		if self.DEBUG > 1:	  # save the entire e-mail message text
			msg_file = '/var/tmp/msg.txt' 
			print 'TD: saving email to %s' % msg_file
			fx = open(msg_file, 'wb')
			fx.write('%s' % msg)
			fx.close()
			try:
				os.chmod(msg_file,S_IRWXU|S_IRWXG|S_IRWXO)
			except OSError:
				pass

		self.db = self.env.get_db_cnx()
		tkt = self.new_ticket(self.env)
		tkt['status'] = 'new'

		# Some defaults
		#
		tkt['milestone'] = self.get_config('ticket', 'default_milestone')
		tkt['priority'] = self.get_config('ticket', 'default_priority')
		tkt['severity'] = self.get_config('ticket', 'default_severity')
		tkt['version'] = self.get_config('ticket', 'default_version')

		if not msg['Subject']:
			tkt['summary'] = '(geen subject)'
		else:
			tkt['summary'] = self.to_unicode(msg['Subject'])

		if self.SPAM_LEVEL and self.spam(msg):
			print 'This message is a SPAM. Automatic ticket insertion refused (SPAM level > %d' % self.SPAM_LEVEL
			sys.exit(1)

		if settings.has_key('component'):
			tkt['component'] = settings['component']
		else:
			tkt['component'] = self.get_config('ticket', 'default_component')

		# Get default owner for component
		#
		cursor = self.db.cursor()
		sql = 'SELECT owner FROM component WHERE name=\'%s\'' % tkt['component']
		cursor.execute(sql)
		tkt['owner'] = cursor.fetchone()[0]

		from_str = self.to_unicode(msg['from'])
		tkt['reporter'] = from_str
		if self.CC:
			tkt['cc'] = from_str

# produce e-mail like header
		head = ''
		if self.EMAIL_HEADER > 0:
			head = self.email_header_txt(msg)

		if self.DEBUG > 0:
			self.debug_attachments(msg)

#
#	put the message text in the ticket description
#	message text can be plain text or html or something else
#
		has_description = 0
		for part in msg.walk():
			if part.get_content_maintype() == 'multipart':			# 'multipart/*' is a container for multipart messages
				continue

			if part.get_content_type() == 'text/plain':
				body_text = part.get_payload(decode=1)			# try to decode
				if not body_text:					# decode failed
					body_text = part.get_payload(decode=0)		# do not decode

				tkt['description'] = '\n{{{\n\n%s\n}}}\n' % body_text

			elif part.get_content_type() == 'text/html':
				tkt['description'] = '%s\n\n(see attachment for HTML mail message)\n' % head
				body_text = tkt['description']

			else:
				tkt['description'] = '%s\n\n(see attachment for message)\n' % head
				body_text = tkt['description']

			has_description = 1
			break		# we have the description, so break

		if not has_description:
			tkt['description'] = '%s\n\n(no plain text message, see attachments)' % head
			has_description = 1

		author, email_addr  = email.Utils.parseaddr(msg['from'])
		if self.MAILTO:
			mailto = self.html_mailto_link(author, email_addr, self.to_unicode(msg['subject']), body_text)
			tkt['description'] = '%s\n%s %s' %(head, mailto, tkt['description'])

		if self.VERSION > 0.8:
			tkt['id'] = tkt.insert()
		else:
			tkt['id'] = tkt.insert(self.db)

		#
		# Just how to show to update description
		#
		#tkt['description'] = '\n{{{\n\n Bas is op nieuw bezig\n\n }}}\n' 
		#tkt.save_changes(self.db, author, "Lekker bezig")
		#
		self.attachments(msg, tkt, author)


	def mail_line(self, str):
		return '%s %s' % (self.comment, str)


	def html_mailto_link(self, author, mail_addr, subject, body):
		if not author:
			author = mail_addr
		else:	
			author = self.to_unicode(author)

		# Must find a fix
		#
		#arr = string.split(body, '\n')
		#arr = map(self.mail_line, arr)

		#body = string.join(arr, '\n')
		#body = '%s wrote:\n%s' %(author, body)

		# Obsolete for reference
		#
		#body = self.to_unicode(body)
		#body = urllib.quote(body)
		#body = Header.encode(body)
		#

		# Temporary fix
		body = '> Type your reply'
		str = 'mailto:%s?subject=%s&body=%s' % (urllib.quote(mail_addr), urllib.quote('Re: %s' % subject), urllib.quote(body))
		str = '\n{{{\n#!html\n<a href="%s">Reply to: %s</a>\n}}}\n' %(str, author)

		return str

	def attachments(self, message, ticket, user):
		'''save any attachments as file in the ticket's directory'''

		count = 0
		first = 0
		for part in message.walk():
			if part.get_content_maintype() == 'multipart':		# multipart/* is just a container
				continue

			if not first:										# first content is the message
				first = 1
				if part.get_content_type() == 'text/plain':		# if first is text, is was already put in the description
					continue

			filename = part.get_filename() 
			if not filename:
				count = count + 1
				filename = 'part%04d' % count

				ext = mimetypes.guess_extension(part.get_type())
				if not ext:
					ext = '.bin'

				filename = '%s%s' % (filename, ext)
			else:
				filename = self.to_unicode(filename)

			if '/' in filename:
				filename = os.path.basename(filename)

			url_filename = urllib.quote(filename)

			if self.VERSION > 0.8:
				tmpfile = '/tmp/email2trac-ticket%sattachment' % str(ticket['id'])
			else:
				dir = os.path.join(self.env.get_attachments_dir(), 'ticket', 
				                    	urllib.quote(str(ticket['id'])))
				if not os.path.exists(dir):
					mkdir_p(dir, 0755)

				tmpfile = os.path.join(dir, url_filename)

			f = open(tmpfile, 'wb')
			text = part.get_payload(decode=1)
			if not text:
				text = '(None)'
			f.write(text)

			# get the filesize
			#
			stats = os.lstat(tmpfile) 
			filesize = stats[stat.ST_SIZE]

			# Insert the attachment it differs for the different TRAC versions
			#
			if self.VERSION > 0.8:
				att = attachment.Attachment(self.env,'ticket',ticket['id'])
				att.insert(url_filename,f,filesize)
				f.close()
			else:
				cursor = self.db.cursor()
				cursor.execute('INSERT INTO attachment VALUES("%s","%s","%s",%d,%d,"%s","%s","%s")' 
					%('ticket', urllib.quote(str(ticket['id'])), filename + '?format=raw', filesize, 
					  int(time.time()),'', user, 'e-mail') ) 
				self.db.commit()


def mkdir_p(dir, mode):
	'''do a mkdir -p'''

	arr = string.split(dir, '/')
	path = ''
	for part in arr:
		path = '%s/%s' % (path, part)
		try:
			stats = os.stat(path)
		except OSError:
			os.mkdir(path, mode)


def ReadConfig(file, name):
	"""
	Parse the config file
	"""

	if not os.path.isfile(file):
		print 'File %s does not exists' %file
		sys.exit(1)

	config = ConfigParser.ConfigParser()
	try:
		config.read(file)
	except ConfigParser.MissingSectionHeaderError,detail:
		print detail
	  	sys.exit(1)


  	# Use given project name else use defaults
  	#
	if name:
		if not config.has_section(name):
			print "Not an valid project name: %s" %name
			print "Valid names: %s" %config.sections()
			sys.exit(1)

		project =  dict()
		for option in  config.options(name):
			project[option] = config.get(name, option) 

	else:
		project = config.defaults()

	return project

if __name__ == '__main__':
	# Default config file
	#
	configfile = '/etc/email2trac.conf'
	# configfile = './email2trac.conf'
	project = ''
	component = ''
	
	try:
		opts, args = getopt.getopt(sys.argv[1:], 'chf:p:', ['component=','help', 'file=', 'project='])
	except getopt.error,detail:
		print __doc__
		print detail
		sys.exit(1)

	project_name = None
	for opt,value in opts:
		if opt in [ '-h', '--help']:
			print __doc__
			sys.exit(0)
		elif opt in ['-c', '--component']:
			component = value
		elif opt in ['-f', '--file']:
			configfile = value
		elif opt in ['-p', '--project']:
			project_name = value

	settings = ReadConfig(configfile, project_name)
	if not settings.has_key('project'):
		print __doc__
		print 'No project defined in config file, eg:\n\t project: /data/trac/bas'
		sys.exit(1)

	if component:
		settings['component'] = component

	if settings.has_key('trac_version'):
		version = float(settings['trac_version'])
	else:
		version = trac_default_version

	#debug HvB
	#print settings

	if version > 0.8:
		from trac import attachment, config, env, ticket
		env = env.Environment(settings['project'], create=0)
		ticket_mod = ticket
	else:
		from trac import Environment, Ticket
		env = Environment.Environment(settings['project'], create=0)
		ticket_mod = Ticket
		
	tktparser = TicketEmailParser(env, settings, version)
	tktparser.parse(sys.stdin)

# EOB
