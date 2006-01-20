/*
	run_email2trac.c
	Authors: Bas van der Vlies, Walter de Jong and Michel Jouvin
	SVN Info:
		$Id$

	Only nobody can become the user www-data. Postfix uses this
	user to start an program

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
*/
#include <stdlib.h>
#include <unistd.h>
#include <pwd.h>
#include <sys/stat.h>
#include <string.h>
#include <stdio.h>

#include "run_email2trac.h"

#ifndef DEBUG
#define DEBUG 0
#endif

int main(int argc, char** argv) {

  int i,j;
  int caller = getuid();
  int status;
  char trac_script[255];
  char** trac_script_args;
  struct passwd *TRAC; 
  struct passwd *MTA;
  struct stat script_attrs;
  
  strcat(trac_script,TRAC_SCRIPT_PATH);
  strcat(trac_script,"/");
  strcat(trac_script,TRAC_SCRIPT_NAME);

  /* First copy arguments passed to the wrapper as scripts arguments
     after filtering out some of the possible script options */
  trac_script_args = (char**) malloc((argc+1)*sizeof(char*));
  trac_script_args[0] = TRAC_SCRIPT_NAME;
  for (i=j=1; i<argc; i++) {
    if ( (strcmp(argv[i],"--file") == 0) || 
	 (strcmp(argv[i],"-f") == 0) ) {
      i++;
      continue;
    }
    
    trac_script_args[j] = argv[i];
    j++;
  }
  trac_script_args[j] = NULL;

  
  /* Check caller */
  
  MTA = getpwnam(MTA_USER);
  if ( caller !=  MTA->pw_uid ) {
    if ( DEBUG ) printf("Invalid caller UID (%d)\n",caller);
    return -2;     /* 254 : Invalid caller */
  }
  
  
  /* set UID/GID to Trac (or apache) user */
  if ( TRAC = getpwnam(TRAC_USER) ) {
    setuid(TRAC->pw_uid);
    setgid(TRAC->pw_gid);
  } else {
    if ( DEBUG ) printf("Invalid Trac user (%s)\n",TRAC_USER);
    return -3;     /* 253 : Trac user not found */
  }
	 
  /* Check that script exists */
  if ( stat(trac_script,&script_attrs) ) {
    if ( DEBUG ) printf("Script not found (%s)\n",trac_script);
    return -4;    /* 252 : script not found */
  }
 
  /* Execute script */
  status = execv(trac_script, trac_script_args);
  if ( DEBUG ) printf("Script %s execution failure (error=%d). Check permission and interpreter path.\n",trac_script,status);
  return -1;     /* 255 : should never reach this point */

}

/* EOB */
