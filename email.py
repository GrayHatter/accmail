#!/usr/bin/env python
import re
import os

UID = re.compile(r"\(UID (\d+) ", re.I)
MID = re.compile(r"^(\d+) ", re.I)
EMAIL = re.compile(r"([^\s\"<]+@gr.ht)>?", re.I)
TO = re.compile(r"\r\nTo:(.+?)\r\n", re.I)
FROM = re.compile(r"\r\nFrom:(.+?)\r\n", re.I)
LIST_A = re.compile(r"\r\nList-Archive:(.+?)\r\n", re.I)
LIST_ID = re.compile(r"\r\nList-Id:(.+?)\r\n", re.I)
to_domain_re = r"([^\s\"<]+@" + os.getenv("ACCMAIL_DOMAIN", "example.com") + r")>?"
TO_DOMAIN = re.compile(to_domain_re, re.I)


class Message():
    def __init__(self, imap, mailbox, blob):
        self.imap = imap
        self._mailbox = mailbox
        self._bblob = blob
        self._blob = blob.decode()
        self.uid = None
        self.mid = None
        self.H = self.headers = {}
        self.parse()

    def __repr__(self):
        return f"Message<From: { self.to }, To: { self.from_ }, List: { self.list_archive }>"

    def parse(self):
        if not all([
            self.imap,
            self._mailbox,
            self._blob,
        ]):
            raise NotImplementedError()

        match = UID.search(self._blob)
        if match:
            self.uid = match.group(1).strip()

        match = MID.search(self._blob)
        if match:
            self.mid = match.group(1).strip()

        match = TO.search(self._blob)
        if match:
            self.to = self._orig_to = match.group(1).strip()
            match = TO_DOMAIN.search(self.to)
            if match:
                self.to = match.group(1).lower().strip()

        match = FROM.search(self._blob)
        if match:
            self.from_ = match.group(1).strip()
        else:
            self.from_ = "Empty"

        match = LIST_A.search(self._blob)
        if match:
            self.list_archive = match.group(1).strip()
        else:
            self.list_archive = "Empty"

        match = LIST_ID.search(self._blob)
        if match:
            self.list_id_full = match.group(1).strip()
            smatch = re.search(r"(.+/.+) ", self.list_id_full)
            if smatch:
                self.list_id = smatch.group(1).strip()
            else:
                self.list_id = self.list_id_full
        else:
            self.list_id_full = self.list_id = "Empty"

    def _FETCH(self, field):
        self.imap.select(self.mailbox)
        res, data = self.imap.uid("FETCH", self.uid, field)
        if res is None:
            # FIXME actually check error code
            raise NotImplementedError()
        return data

    @property
    def subject(self):
        return self.subject

    def _FLAG(self, action, flags):
        self.imap.select(self._mailbox)
        res, data = self.imap.uid("STORE", self.uid, action, flags)
        return res, data

    def add_flag(self, flag):
        return self._FLAG("+FLAGS", flag)

    def del_flag(self, flag):
        return self._FLAG("-FLAGS", flag)

    def delete(self):
        res = self.add_flag("\\Deleted")
        return res

    def copy(self, target_mb):
        if target_mb == self._mailbox:
            raise ValueError("SRC and DST mailbox are the same")
        self.imap.select(self._mailbox)
        res, data = self.imap.uid("COPY", self.uid, target_mb)
        return res, data

    def move(self, target_mb):
        print(f"moving {self.uid} ({self.to}) {self._mailbox} into {target_mb}")
        #self.copy(target_mb)
        #self.delete()

