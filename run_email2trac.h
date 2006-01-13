/*
Local site configuration
Value defined here are just default values than can be overriden at compile time
See Makefile.
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

