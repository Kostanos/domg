import ast
import glob
import os

__author__ = 'cosmin'


class DockerfileParser(object):
    KEYWORDS = "FROM MAINTAINER RUN CMD COPY EXPOSE ENV ADD ENTRYPOINT VOLUME USER WORKDIR ONBUILD".split(" ")
    COMMENT_START = "#"
    COMMENT_KEYWORDS = "LINK ENV".split(" ")
    LINE_CONTINUATION = "\\"
    CONFIGURABLE_KEYWORDS = "CMD ENTRYPOINT EXPOSE VOLUME LINK ENV".split(" ")

    def __init__(self, dockerfile, configurable_keywords=None):
        if not os.path.isfile(dockerfile):
            self.dockerfile = dockerfile.split('\n')
        else:
            with open(dockerfile) as f:
                self.dockerfile = f.readlines()
        self._cleanup()
        self.config = {}
        if configurable_keywords is not None:
            self.CONFIGURABLE_KEYWORDS = configurable_keywords

    def get_config(self):
        if not self.config:
            self.config = self._parse()
        return self.config

    def all(self):
        return self.get_config()

    def get(self, keyword):
        config = self.get_config()
        return config[keyword] if keyword in config else None

    def configurable(self):
        config = self.get_config()
        return {keyword: config[keyword] for keyword in config if keyword in self.CONFIGURABLE_KEYWORDS}

    def _cleanup(self):
        newlist = []
        joined_lines = ''
        for l in self.dockerfile:
            l = l.strip()
            if l == '':
                continue
            if l[0] == self.COMMENT_START:
                comment = l[1:].split(' ')
                if comment[0] not in self.COMMENT_KEYWORDS:
                    continue
                l = l[1:]
            if l[-1] == self.LINE_CONTINUATION:
                joined_lines += l[:-1]
                continue
            elif joined_lines:
                l = joined_lines + l
                joined_lines = ''
            newlist.append(l)
        self.dockerfile = newlist

    def _parse(self):
        if len(self.dockerfile) == 1 and self.dockerfile[0][0:4] != 'FROM':
            raise Exception('Invalid Dockerfile: %s' % self.dockerfile)
        config = {}
        for line in self.dockerfile:
            kw, arg = line.split(' ', 1)
            if kw not in self.KEYWORDS and kw not in self.COMMENT_KEYWORDS:
                continue
            arg = arg.strip()
            if arg[0] == '[' and arg[-1] == ']':
                arg = ast.literal_eval(arg)
            if kw in config:
                config[kw].append(arg)
            else:
                if isinstance(arg, list):
                    config[kw] = arg
                else:
                    config[kw] = [arg]
        return config


def finder(path):
    if not os.path.isdir(path):
        return []
    os.chdir(path)
    return [dockerfile for dockerfile in glob.glob("*/Dockerfile")]