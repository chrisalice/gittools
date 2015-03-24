import re, sh, travispy, warnings
from collections import defaultdict
from multiprocessing.pool import ThreadPool
from travispy import TravisPy
from utils import Branch, lazy

class TravisClient(object):

  SLUG_REGEX = re.compile('^git[@]github[.]com:(.*)[.]git$')

  @lazy
  def _githubToken(self):
    return str(sh.git.config('github.token', _tty_out=False)).strip()

  @lazy
  def _remoteSlugs(self):
    """Remote 'slug' of any GitHub repos, keyed by remote name."""
    try:
      raw = sh.git.config('--get-regexp', 'remote\..*\.url', _tty_out=False, _iter=True)
      remotes = {}
      for l in raw:
        key, url = l.strip().split(' ', 1)
        name = key.split('.', 1)[-1].rsplit('.', 1)[0]
        slug_match = TravisClient.SLUG_REGEX.match(url)
        if slug_match:
          remotes[name] = slug_match.group(1)
      return remotes
    except sh.ErrorReturnCode_1:
      return {}

  @lazy
  def _remotesByBranchName(self):
    remotes = defaultdict(set)
    for remoteBranch in Branch.REMOTES:
      remote, branchName = remoteBranch.name.split('/', 1)
      if remote in self._remoteSlugs:
        remotes[branchName].add(remote)
    return remotes

  @lazy
  def _travis(self):
    with warnings.catch_warnings():
      warnings.filterwarnings('ignore', message='.*InsecurePlatformWarning.*')
      return TravisPy.github_auth(self._githubToken)

  @lazy
  def _ciStatuses(self):
    try:
      pool = ThreadPool(20)
      with warnings.catch_warnings():
        warnings.filterwarnings('ignore', message='.*InsecurePlatformWarning.*')
        status = defaultdict(dict)
        todos = ((branch, remote) 
                 for branch, remotes in self._remotesByBranchName.iteritems()
                 for remote in remotes)
        def fetchStatus(todo):
          branch, remote = todo
          slug = self._remoteSlugs[remote]
          try:
            b = self._travis.branch(branch, slug)
            status[branch][remote] = b.color
          except travispy.errors.TravisError, e:
            pass
        pool.map(fetchStatus, todos)
        return status
    except IOError:
      return defaultdict(dict)

  def ciStatus(self, branch):
    return self._ciStatuses[branch.name]
