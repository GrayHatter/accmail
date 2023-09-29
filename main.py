#!/usr/bin/env python
import imaplib
import os
import sieve
import email

DEBUG = True


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

def my_domain(t, domain=None):
    if domain is None:
        domain = os.getenv('ACCMAIL_DOMAIN');
    return domain in t

def main():
    moves = {}
    lists = {}
    autodrops = []
    unknowns = set()

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

        DEF_SEARCH = "(UID BODY[HEADER.FIELDS (TO FROM LIST-ARCHIVE LIST-ID)])"

        for folder in f_folders:
            conn.select(folder, True)
            res, search = conn.search(None, "ALL")
            out = search[0].decode().replace(' ', ',')
            res, data = conn.fetch(out, DEF_SEARCH)

            f_folders[folder] = data_to_msg(conn, folder, data)

            for each in sorted(set([m.to for m in f_folders[folder]])):
                if my_domain(each):
                    moves[each] = folder
                else:
                    unknowns.add(each)

            for each in sorted(set([m for m in f_folders[folder]]), key=lambda x: x.to):
                if each.list_archive != "Empty" and not my_domain(each.to):
                    lists[each.list_archive] = folder

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
                    # m.move(moves[m.to])
                    pass
                elif f"@{os.getenv('ACCMAIL_DOMAIN')}" in m.to:
                    unknowns.add(m.to)
            # res, data = conn.expunge()

        if DEBUG:
            for each in moves:
                print(f"Known Email: {each}")
            for each, fold in lists.items():
                print(f"Known list: {each}, {fold}")
            for each in unknowns:
                print(f"Unknowns: {each}")
            for ms in list(f_folders.values()) + list(folders.values()):
                for m in ms:
                    if m.list_archive == "Empty":
                        continue
                    print(m, m.list_id, m.list_id_full)


if __name__ == "__main__":
    main()

