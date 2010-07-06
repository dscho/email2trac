Summary: Utilities for converting emails to trac tickets
Name: email2trac
Version: 1.4.8
Release: 1
License: GPL
Group: Applications/Internet
URL: https://subtrac.sara.nl/oss/email2trac

Packager: Jon Topper <jon@topper.me.uk>

Source: ftp://ftp.sara.nl/pub/outgoing/email2trac.tar.gz

BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root

Requires: trac

%description
This is a release of the SARA package email2trac that contains utilities that we use to convert emails to trac tickets. The initial setup was made by Daniel Lundin from Edgewall Software. SARA has extend the initial setup, with the following extensions:

    * HTML messages
    * Attachments
    * Use commandline options
    * Use config file to change the behaviour of the email2trac.py program
    * Some unicode support for special characters in the headers of an email message 

%prep
rm -rf $RPM_BUILD_ROOT
%setup
%configure

%build
mkdir -p $RPM_BUILD_ROOT
make

%install
make DESTDIR="$RPM_BUILD_ROOT" install

%files
/usr/bin/delete_spam
/usr/bin/email2trac
/usr/bin/run_email2trac
%config /etc/email2trac.conf

%changelog
* Thu Aug 03 2006 Jon Topper <jon@topper.me.uk> - 0.7.6-1
- Initial RPM build
