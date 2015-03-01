
### Backup Your Wordpress Blog Using Python

A Tool to easily backup Wordpress posts to your local filesystem.

I use this together with [local-blog](https://github.com/pklaus/local-blog)
to host a local copy of my own blog on my laptop (for use on the road etc.).

#### Usage

    usage: backup-wordpress-blog.py [-h] [--username USERNAME]
                                    [--password PASSWORD] [--folder FOLDER]
                                    [--number NUMBER] [--long-filenames]
                                    [--no-meta] [--media] [--debug]
                                    [--extension EXTENSION]
                                    BLOG_URL
    
    Backing up the blog posts of a Wordpress blog to your local file system.
    
    positional arguments:
      BLOG_URL              The URL of your Wordpress Blog
    
    optional arguments:
      -h, --help            show this help message and exit
      --username USERNAME, -u USERNAME
                            Username used to login to your blog.
      --password PASSWORD, -p PASSWORD
                            Password used to login to your blog.
      --folder FOLDER, -f FOLDER
                            Folder to store the backups of the blog posts (./).
      --number NUMBER, -n NUMBER
                            Number of blog posts to back up (default is 4000).
      --long-filenames, -l  Use extended filenames for the blog post backup files.
      --no-meta             Don't store any meta information (such as tags) in the
                            backup files.
      --media               Also backup media files and their metadata.
      --debug, -d           Run in debug mode (used by the developer).
      --extension EXTENSION, -e EXTENSION
                            The file extension of the backed up blog post files
                            (default is txt).
