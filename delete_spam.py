#!/usr/bin/python
#
# Copyright (C) 2002
#
# This file is part of the pxeconfig utils
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
Author: Bas van der Vlies
Date  : 29 September 2205
Desc. : Delete Spam tickets from database. Else we get an lot of 
        tickets

Usage :
	delete_spam [ -f <configfile> ]

defaults:
	configfile = /etc/email2trac.conf

SVN Info:
        $Id: delete_spam.py 1512 2005-10-26 09:20:37Z jaap $
"""
from trac import Environment, Ticket

import os
import sys
import getopt
import shutil
import ConfigParser

def ReadConfig(file):
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

	defaults = config.defaults()
	if not defaults.has_key('project'):
		print 'You have define the location of your trac project, eg:'
		print '\t project: /var/trac/<projectname>'
		sys.exit(1)
	  
	return defaults


def delete_spam(project, debug):
			env = Environment.Environment(project, create=0)
			db = env.get_db_cnx()
			
			cursor = db.cursor()

			# Delete the attachments associated with Spam tickets
			#
			cursor.execute("SELECT id FROM ticket WHERE  component = 'Spam';") 
			while 1:
				row = cursor.fetchone()
				if not row:
					break
				spam_id =  row[0]
				attachment_dir = os.path.join(env.get_attachments_dir(), 'ticket', str(spam_id)) 
				if os.path.exists(attachment_dir):
					if debug:
						print 'delete %s : %s' %(spam_id, attachment_dir)
					shutil.rmtree(attachment_dir)

			cursor.execute("DELETE FROM ticket WHERE  component = 'Spam';") 
			db.commit()

if __name__ == '__main__':
	# Default config file
	#
	configfile = '/etc/email2trac.conf'

	try:
		 opts, args = getopt.getopt(sys.argv[1:], 'hf:', ['help', 'file='])
	except getopt.error,detail:
		print __doc__
		print detail
		sys.exit(1)

	for opt,value in opts:
		if opt in [ '-h', '--help']:
			print __doc__ 
			sys.exit(0) 
		elif opt in ['-f', '--file']:
			configfile = value
	
	settings = ReadConfig(configfile)
	delete_spam(settings['project'], int(settings['debug']))
	print 'Spam is deleted succesfully..' 

# EOB
