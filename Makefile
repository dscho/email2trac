# email2trac Makefile
#
# defaullt values are:
#
# MTA_USER "nobody"
# TRAC_USER "www-data"
# TRAC_SCRIPT_NAME "email2trac.py"
# INSTALL_DIR "/usr/bin"
#
MTA_USER=daemon
TRAC_USER=apache
TRAC_SCRIPT_NAME=email2trac.py
INSTALL_DIR=/www/Web/servers/trac/site-config/scripts
PYTHON_BIN=/usr/local/Python/pro/bin/python

CC=cc
DEBUG=0
CFLAGS=-c99 -DMTA_USER=\"$(MTA_USER)\" -DTRAC_USER=\"$(TRAC_USER)\" -DTRAC_SCRIPT_NAME=\"$(TRAC_SCRIPT_NAME)\" -DTRAC_SCRIPT_PATH=\"$(INSTALL_DIR)\" -DDEBUG=$(DEBUG)

PYTHON_FILES=delete_spam.py email2trac.py
WRAPPER_SRC=run_email2trac.c run_email2trac.h

all: run_email2trac

run_email2trac: $(WRAPPER_SRC)
	$(CC) $(CFLAGS) -o $@ run_email2trac.c

install: all
	cp run_email2trac $(INSTALL_DIR)
	chmod u+s $(INSTALL_DIR)/run_email2trac
	chown root $(INSTALL_DIR)/run_email2trac
	for script in $(PYTHON_FILES) ; \
	do \
	  sed -e "s%^\#\!/usr/bin/python%\#\!$(PYTHON_BIN)%" $$script > $(INSTALL_DIR)/$$script ; \
	  chmod a+x $(INSTALL_DIR)/$$script ; \
	done
