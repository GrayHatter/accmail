#!/usr/bin/env python
import imaplib
import os
import sieve
import email


def data_to_msg(conn, mailbox, data):
    folder = []
    collect = []
    for each in data:
        if each == b')':
            collect.append(each)
            blob = b"\r\n".join(collect)
            folder.append(email.Message(conn, mailbox, blob))
            collect = []
            continue
        collect += list(each)
    return folder


def main():
    moves = {}
    autodrops = []

    with imaplib.IMAP4_SSL(os.environ["ACCMAIL_HOST"]) as conn:
        conn.login(os.getenv("ACCMAIL_USER", ""), os.getenv("ACCMAIL_PASS", ""))
        conn.enable("UTF8=ACCEPT")
        res, dirl = conn.list()

        f_folders = {
            "INBOX": [],
            "2nd": [],
            "3rd": [],
            "4th": [],
        }

        folders = {
            "bulk": [],
            "junk": [],
        }

        DEF_SEARCH = "(UID BODY[HEADER.FIELDS (TO FROM)])"

        for folder in f_folders:
            conn.select(folder, True)
            res, search = conn.search(None, "ALL")
            out = search[0].decode().replace(' ', ',')
            res, data = conn.fetch(out, DEF_SEARCH)

            f_folders[folder] = data_to_msg(conn, folder, data)

            for each in sorted(set([m.to for m in f_folders[folder]])):
                if f"@{os.getenv('ACCMAIL_DOMAIN')}" in each:
                    moves[each] = folder

        for folder in folders:
            conn.select(folder, True)
            res, search = conn.search(None, "ALL")
            out = search[0].decode().replace(' ', ',')
            res, data = conn.fetch(out, DEF_SEARCH)

            folders[folder] = data_to_msg(conn, folder, data)

        for folder in ['autodrop']:
            conn.select(folder, True)
            res, search = conn.search(None, "ALL")
            out = search[0].decode().replace(' ', ',')
            if not len(out):
                continue

            res, data = conn.fetch(out, DEF_SEARCH)

            for each in data_to_msg(conn, folder, data):
                autodrops.append(each.to)

        with open(os.getenv("ACCMAIL_SIEVE", "dovecot.sieve"), "w") as fh:
            fh.write(sieve.generate(moves, autodrops))

        for folder, msgs in folders.items():
            for m in msgs:
                if m.to in moves and moves[m.to] != folder:
                    m.move(moves[m.to])
            res, data = conn.expunge()


if __name__ == "__main__":
    main()

