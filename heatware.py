#!/usr/bin/env python2

import praw
import re
import config

from log_conf import LoggerManager

logger = None


def main():
    try:
        reddit_api = login_to_reddit_api()

        for comment in get_heatware_submission_root_comments(reddit_api):
            add_flair_to_comment_author(reddit_api, comment)

    except Exception as e:
        logger.error(e)
        raise


def login_to_reddit_api():
    logger.debug('Logging in as /u/' + config.reddit.username)
    return praw.Reddit(client_id=config.reddit.app_key,
                       client_secret=config.reddit.app_secret,
                       username=config.reddit.username,
                       password=config.reddit.password,
                       user_agent=config.reddit.username)


def get_heatware_submission_root_comments(reddit_api):
    submission = reddit_api.submission(id=config.heatware.link_id)
    submission.comments.replace_more(limit=None, threshold=0)
    return (comment
            for comment in submission.comments.list()
            if comment.is_root)


def add_flair_to_comment_author(reddit_api, comment):
    logger.debug("Processing comment: " + comment.id)

    if should_not_add_flair_to_author(comment):
        return

    heatware_url = extract_heatware_url_from(comment)

    if heatware_url and bot_has_not_already_replied_to(comment):
        set_author_flair(reddit_api, comment, heatware_url)
        reply_to(comment)


def should_not_add_flair_to_author(comment):
    author_attr_not_present = not hasattr(comment, 'author')
    author_attr_is_empty = hasattr(comment, 'author') and not comment.author
    author_already_has_flair = bool(comment.author_flair_text)
    return (author_attr_not_present or
            author_attr_is_empty or
            author_already_has_flair)


def extract_heatware_url_from(comment):
    match = re.search(config.heatware.regex, comment.body)
    if match:
        return match.group(0)


def bot_has_not_already_replied_to(comment):
    for reply in comment.replies.list():
        if reply.author and str(reply.author.name) == config.reddit.username:
            return False

    return True


def set_author_flair(reddit_api, comment, heatware_url):
    author_flair_css_class = comment.author_flair_css_class or ''
    subreddit = reddit_api.subreddit(config.reddit.subreddit)
    subreddit.flair.set(comment.author,
                        heatware_url,
                        author_flair_css_class)

    logger.info('Set ' + comment.author.name + '\'s heatware to ' + heatware_url)


def reply_to(comment):
    if config.heatware.reply:
        comment.reply(config.heatware.reply)


if __name__ == '__main__':
    logger = LoggerManager().getLogger(__name__)
    main()
