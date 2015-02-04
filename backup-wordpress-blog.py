#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Written on 2013-01-16 by Philipp Klaus <philipp.l.klaus →AT→ web.de>.
Check <https://gist.github.com/4546743> for newer versions.

Install the dependencies python-wordpress-xmlrpc and unidecode using
     pip install python-wordpress-xmlrpc unidecode
"""

try:
    from wordpress_xmlrpc import Client
    from wordpress_xmlrpc.methods import posts
    from wordpress_xmlrpc.methods import users
    from wordpress_xmlrpc.exceptions import InvalidCredentialsError

    import unidecode
except ImportError:
    print("You need to install python-wordpress-xmlrpc and unidecode using pip first. Exiting")
    import sys; sys.exit(1)

import datetime as dt
import argparse, os, errno, sys, time, re

def login(site, user, password=None):
    if not user:
        user = input('Please enter the username for the blog %s: ' % site)
    if not password:
        password = input('Please enter the password for the user %s: ' % user)
    return Client(site, user, password)

def sanitize_url(url):
    if not (url.startswith('http://') or url.startswith('https://')):
        url = 'http://' + url
    if not url.endswith('xmlrpc.php'):
        if not url.endswith('/'):
            url += '/'
        url += 'xmlrpc.php'
    return url

def ensure_folder_exists(folder):
    try:
        os.makedirs(folder)
    except OSError as e:
        if not e.errno == errno.EEXIST:
            raise

def post_file_name(post, short=True, extension='txt'):
    status = post.post_status
    slug = post.slug
    if len(slug) == 0 and len(post.title) > 0:
        title = post.title
        # http://stackoverflow.com/a/8366771/183995
        slug = re.sub(r'\W+', '-', unidecode.unidecode(title).lower())
    if short:
        stati = {'draft': 'd', 'private': 'pr', 'publish': 'p'}
        try:
            status = stati[status]
        except:
            pass
        when = post.date.date().isoformat().replace('-','')
        return '%s_%s_%s.%s' % (status, when, slug[:22], extension)
    else:
        when = post.date.isoformat().replace('T','_').replace(':','-')
        return '%s_%s_%s.%s' % (status, when, slug, extension)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Backing up the blog posts of a Wordpress blog to your local file system.')
    parser.add_argument('url', metavar='BLOG_URL',
                        help='The URL of your Wordpress Blog')
    parser.add_argument('-u', '--username',
                        help='Username used to login to your blog.')
    parser.add_argument('-p', '--password',
                        help='Password used to login to your blog.')
    parser.add_argument('-f', '--folder', default='./',
                        help='Folder to store the backups of the blog posts (./).')
    parser.add_argument('-n', '--number', type=int, default=2000,
                        help='Number of blog posts to back up (2000).')
    parser.add_argument('-l', '--long-filenames', action='store_true',
                        help='Use extended filenames for the blog post backup files.')
    parser.add_argument('-m', '--no-meta', action='store_true',
                        help="Don't store any meta information (such as tags) in the backup files.")
    parser.add_argument('-d', '--debug', action='store_true',
                        help='Run in debug mode (used by the developer).')
    parser.add_argument('-e', '--extension', default='txt',
                        help='The file extension of the backed up blog post files (txt).')
    args = parser.parse_args()

    site = sanitize_url(args.url)

    wp = login(site, args.username, args.password)

    try:
        wp.call(users.GetUserInfo())
    except InvalidCredentialsError:
        print("Invalid credentials")
        sys.exit(1)

    if args.debug: print("Fetching posts now...")
    posts = wp.call(posts.GetPosts({'number': args.number,}))
    if args.debug: print("Fetched {} posts. Saving them now...".format(len(posts)))

    folder = os.path.abspath(args.folder)
    #folder = os.path.join(folder, dt.date.today().isoformat())

    ensure_folder_exists(folder)

    for post in posts:
        tags = [t.name for t in post.terms if t.taxonomy == 'post_tag']
        categories = [t.name for t in post.terms if t.taxonomy == 'category']
        fname = post_file_name(post, short=(not args.long_filenames), extension=args.extension)
        fname = os.path.join(folder, fname)
        f = open(fname, 'w')
        if not args.no_meta:
            # Or YAML Style Frontmatter
            # inspired by http://egonschiele.github.io/mdpress/
            # See http://jekyllrb.com/docs/frontmatter/
            # and http://en.wikipedia.org/wiki/YAML#Lists
            f.write('# %s\n\n' % post.title)
            f.write('* Categories: %s\n' % ', '.join(categories))
            f.write('* Tags: %s\n' % ', '.join(tags))
            f.write('* Creation Date: %s\n' % post.date.isoformat())
            f.write('* Modification Date: %s\n' % post.date_modified.isoformat())
            f.write('* Link: <%s>\n' % post.link)
            f.write('\n### Content\n\n')
        f.write(post.content)
        f.close()
        cr_time = time.mktime(post.date.timetuple())
        os.utime(fname, (cr_time, cr_time))

    print("Successfully backed up %d blog posts." % len(posts))
