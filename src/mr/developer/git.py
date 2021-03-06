from mr.developer import common
import os
import subprocess
import sys


logger = common.logger


class GitError(common.WCError):
    pass


class GitWorkingCopy(common.BaseWorkingCopy):
    def git_checkout(self, source, **kwargs):
        name = source['name']
        path = source['path']
        url = source['url']
        if os.path.exists(path):
            logger.info("Skipped cloning of existing package '%s'." % name)
            return
        logger.info("Cloning '%s' with git." % name)
        cmd = subprocess.Popen(["git", "clone", "--quiet", url, path],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
        stdout, stderr = cmd.communicate()
        if cmd.returncode != 0:
            raise GitError("git cloning for '%s' failed.\n%s" % (name, stderr))
        if kwargs.get('verbose', False):
            return stdout

    def git_update(self, source, **kwargs):
        name = source['name']
        path = source['path']
        logger.info("Updating '%s' with git." % name)
        cmd = subprocess.Popen(["git", "pull"],
                               cwd=path,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
        stdout, stderr = cmd.communicate()
        if cmd.returncode != 0:
            raise GitError("git pull for '%s' failed.\n%s" % (name, stderr))
        if kwargs.get('verbose', False):
            return stdout

    def checkout(self, source, **kwargs):
        name = source['name']
        path = source['path']
        update = self.should_update(source, **kwargs)
        if os.path.exists(path):
            if update:
                self.update(source, **kwargs)
            elif self.matches(source):
                logger.info("Skipped checkout of existing package '%s'." % name)
            else:
                raise GitError("Checkout URL for existing package '%s' differs. Expected '%s'." % (name, source['url']))
        else:
            return self.git_checkout(source, **kwargs)

    def matches(self, source):
        name = source['name']
        path = source['path']
        cmd = subprocess.Popen(["git", "remote", "-v"],
                               cwd=path,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
        stdout, stderr = cmd.communicate()
        if cmd.returncode != 0:
            raise GitError("git remote for '%s' failed.\n%s" % (name, stderr))
        return (source['url'] in stdout.split())

    def status(self, source, **kwargs):
        name = source['name']
        path = source['path']
        cmd = subprocess.Popen(["git", "status"],
                               cwd=path,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
        stdout, stderr = cmd.communicate()
        lines = stdout.strip().split('\n')
        if 'nothing to commit (working directory clean)' in lines[-1]:
            status = 'clean'
        else:
            status = 'dirty'
        if kwargs.get('verbose', False):
            return status, stdout
        else:
            return status

    def update(self, source, **kwargs):
        name = source['name']
        path = source['path']
        force = kwargs.get('force', False)
        status = self.status(source)
        if status != 'clean' and not force:
            print >>sys.stderr, "The package '%s' is dirty." % name
            while 1:
                answer = raw_input("Do you want to update it anyway [y/N]? ")
                if answer.lower() in ('', 'n', 'no'):
                    break
                elif answer.lower() in ('y', 'yes'):
                    force = True
                    break
                else:
                    print >>sys.stderr, "You have to answer with y, yes, n or no."
        if not self.matches(source):
            raise GitError("Can't update package '%s', because it's URL doesn't match." % name)
        if status != 'clean' and not force:
            raise GitError("Can't update package '%s', because it's dirty." % name)
        return self.git_update(source, **kwargs)

wc = GitWorkingCopy('git')
