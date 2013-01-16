#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

"""
Written on 2013-01-16 by Philipp Klaus <philipp.l.klaus →AT→ web.de>.
Check <https://gist.github.com/4546743> for newer versions.

Install the dependency python-wordpress-xmlrpc using
     pip install python-wordpress-xmlrpc
"""

from wordpress_xmlrpc import Client
from wordpress_xmlrpc.methods import posts
from wordpress_xmlrpc.methods import users

import datetime as dt

import argparse, os, errno

def login(site, user):
    if not user:
        user = raw_input('Please enter the username for the blog %s: ' % site)
    password = raw_input('Please enter the password for the user %s: ' % user)
    return Client(site, user, password)

def sanitize_url(url):
    if not (url.startswith('http://') or url.startswith('https://')):
        url = 'http://' + url
    if not url.endswith('xmlrpc.php'):
        if not url.endswith('/'):
            url += '/'
        url += 'xmlrpc.php'
    return url

def post_file_name(post, short=True, extension='txt'):
    status = post.post_status
    stati = {'draft': 'd', 'private': 'pr', 'publish': 'p'}
    try:
        status = stati[status]
    except:
        pass
    if short:
        when = post.date.date().isoformat().replace('-','')
        return '%s_%s_%s.%s' % (status, when, post.slug[:16], extension)
    else:
        when = post.date.isoformat().replace('T','_').replace(':','-')
        '%s_%s_%s.%s' % (status, when, post.slug, extension)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Backing up the blog posts of a Wordpress blog to your local file system.')
    parser.add_argument('url', metavar='BLOG_URL',
                        help='The URL of your Wordpress Blog')
    parser.add_argument('-u', '--username',
                        help='Username used to login to your blog.')
    parser.add_argument('-f', '--folder', default='./',
                        help='Folder to store the backups of the blog posts (./).')
    parser.add_argument('-n', '--number', type=int, default=2000,
                        help='Number of blog posts to back up (2000).')
    parser.add_argument('-d', '--debug', action='store_true',
                        help='Run in debug mode (used by the developer).')
    args = parser.parse_args()

    site = sanitize_url(args.url)
    user = args.username

    wp = login(site, user)

    #print wp.call(users.GetUserInfo())

    posts = wp.call(posts.GetPosts({'number': args.number,}))

    folder = args.folder
    #folder = os.path.join(folder, dt.date.today().isoformat())
    try:
        os.makedirs(folder)
    except OSError, e:
        if not e.errno == errno.EEXIST:
            raise

    for post in posts:
        if args.debug:
            print post.sticky
            continue
        fname = post_file_name(post)
        f = open(os.path.join(folder, fname ), 'w')
        f.write('# %s\n\n' % post.title.encode('utf-8'))
        f.write(post.content.encode('utf-8'))
        f.close()
        cr_time = time.mktime(post.date.timetuple())
        os.utime(fname, (cr_time, cr_time))

    print "Backed up %d blog posts." % len(posts)
