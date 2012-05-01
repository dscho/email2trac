/*

SVN Info:
    $Id$

Local site configuration
Value defined here are just default values than can be overriden at compile time
See Makefile.

       Licensed to the Apache Software Foundation (ASF) under one
       or more contributor license agreements.  See the NOTICE file
       distributed with this work for additional information
       regarding copyright ownership.  The ASF licenses this file
       to you under the Apache License, Version 2.0 (the
       "License"); you may not use this file except in compliance
       with the License.  You may obtain a copy of the License at

         http://www.apache.org/licenses/LICENSE-2.0

       Unless required by applicable law or agreed to in writing,
       software distributed under the License is distributed on an
       "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
       KIND, either express or implied.  See the License for the
       specific language governing permissions and limitations
       under the License.
*/

/* User the MTA is running under */
#ifndef MTA_USER
#define MTA_USER "nobody"
#endif

/* A user with write access to Trac DB */
#ifndef TRAC_USER
#define TRAC_USER "www-data"
#endif

/* email2trac script name and path */
#ifndef TRAC_SCRIPT_NAME
#define TRAC_SCRIPT_NAME "email2trac"
#endif
#ifndef TRAC_SCRIPT_PATH
#define TRAC_SCRIPT_PATH "/usr/bin"
#endif
