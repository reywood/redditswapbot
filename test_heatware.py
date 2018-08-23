from mock import Mock, patch
from unittest import TestCase

# import heatware_old as heatware  # noqa
import heatware


@patch('praw.Reddit', autospec=True)
class HeatwareTest(TestCase):
    def setUp(self):
        heatware.logger = Mock()

        self.original_config = heatware.config
        mock_config = Mock()
        mock_config.reddit.app_key = 'fake app key'
        mock_config.reddit.app_secret = 'fake app secret'
        mock_config.reddit.username = 'fake username'
        mock_config.reddit.password = 'fake password'
        mock_config.heatware.regex = '^.+$'
        heatware.config = mock_config

    def tearDown(self):
        heatware.config = self.original_config

    def test_login_to_reddit_with_values_from_config(self, MockReddit):
        mock_reddit_api = self._setup_mock_reddit_api(MockReddit)
        self._add_a_mock_comment_to_heatware_submission(mock_reddit_api)

        heatware.main()

        heatware.praw.Reddit.assert_called_with(client_id='fake app key',
                                                client_secret='fake app secret',
                                                username='fake username',
                                                password='fake password',
                                                user_agent='fake username')

    def test_should_add_flair_to_comment_author(self, MockReddit):
        mock_reddit_api = self._setup_mock_reddit_api(MockReddit)
        mock_comment = self._add_a_mock_comment_to_heatware_submission(mock_reddit_api)

        heatware.main()

        self._assert_flair_added_to_comment_author(mock_reddit_api, mock_comment)

    def test_should_not_add_flair_to_comment_author_if_author_already_has_flair(self, MockReddit):
        mock_reddit_api = self._setup_mock_reddit_api(MockReddit)
        mock_comment = self._add_a_mock_comment_to_heatware_submission(mock_reddit_api)

        mock_comment.author_flair_text = 'existing flair'

        heatware.main()

        self._assert_flair_not_added_to_author(mock_reddit_api)

    def test_should_not_add_flair_if_author_attribute_not_present(self, MockReddit):
        mock_reddit_api = self._setup_mock_reddit_api(MockReddit)
        mock_comment = self._add_a_mock_comment_to_heatware_submission(mock_reddit_api)

        delattr(mock_comment, 'author')

        heatware.main()

        self._assert_flair_not_added_to_author(mock_reddit_api)

    def test_should_not_add_flair_if_author_attribute_is_empty(self, MockReddit):
        mock_reddit_api = self._setup_mock_reddit_api(MockReddit)
        mock_comment = self._add_a_mock_comment_to_heatware_submission(mock_reddit_api)

        mock_comment.author = None

        heatware.main()

        self._assert_flair_not_added_to_author(mock_reddit_api)

    def test_should_not_add_flair_if_comment_body_does_not_match_pattern(self, MockReddit):
        mock_reddit_api = self._setup_mock_reddit_api(MockReddit)
        mock_comment = self._add_a_mock_comment_to_heatware_submission(mock_reddit_api)

        heatware.config.heatware.regex = '^body must match this$'
        mock_comment.body = 'invalid'

        heatware.main()

        self._assert_flair_not_added_to_author(mock_reddit_api)

    def test_should_not_add_flair_if_swapbot_has_already_replied_to_comment(self, MockReddit):
        mock_reddit_api = self._setup_mock_reddit_api(MockReddit)
        mock_comment = self._add_a_mock_comment_to_heatware_submission(mock_reddit_api)

        self._add_swapbot_reply_to_comment(mock_comment)

        heatware.main()

        self._assert_flair_not_added_to_author(mock_reddit_api)

    def test_should_add_flair_if_swapbot_has_not_already_replied_to_comment_but_someone_else_has(self, MockReddit):
        mock_reddit_api = self._setup_mock_reddit_api(MockReddit)
        mock_comment = self._add_a_mock_comment_to_heatware_submission(mock_reddit_api)

        self._add_reply_to_comment(mock_comment, 'janedoe')

        heatware.main()

        self._assert_flair_added_to_comment_author(mock_reddit_api, mock_comment)

    # def test_should_only_add_flair_to_root_comments(self, MockReddit):
    #     mock_reddit_api = self._setup_mock_reddit_api(MockReddit)
    #     mock_comment = self._add_a_mock_comment_to_heatware_submission(mock_reddit_api)

    #     mock_reply = self._add_reply_to_comment(mock_comment, 'janedoe')

    #     heatware.main()

    #     self._assert_flair_added_to_comment_author(mock_reddit_api, mock_comment)

    def _setup_mock_reddit_api(self, MockReddit):
        mock_reddit_api = Mock()
        MockReddit.return_value = mock_reddit_api

        mock_reddit_api.subreddit.return_value = Mock()

        return mock_reddit_api

    def _add_a_mock_comment_to_heatware_submission(self, mock_reddit_api):
        mock_comment = self._create_mock_comment()

        mock_submission = mock_reddit_api.submission.return_value
        mock_submission.comments.list.return_value = [mock_comment]

        return mock_comment

    def _add_swapbot_reply_to_comment(self, mock_comment):
        self._add_reply_to_comment(mock_comment, heatware.config.reddit.username)

    def _add_reply_to_comment(self, mock_comment, reply_author):
        reply = self._create_mock_comment(is_root=False, author_name=reply_author)

        mock_comment.replies.list.return_value = [reply]

        return reply

    def _create_mock_comment(self, id_='', is_root=True, author_name=''):
        mock_comment = Mock()
        mock_comment.id = id_
        mock_comment.is_root = is_root
        mock_comment.body = 'https://www.heatware.com/u/12345'

        mock_author = Mock()
        mock_author.name = author_name
        mock_comment.author = mock_author
        mock_comment.author_flair_text = None
        mock_comment.author_flair_css_class = 'fake-flair-css-class'

        mock_comment.replies.list.return_value = []

        return mock_comment

    def _assert_flair_added_to_comment_author(self, mock_reddit_api, mock_comment):
        mock_subreddit = mock_reddit_api.subreddit.return_value
        assert mock_subreddit.flair.set.call_count == 1
        mock_subreddit.flair.set.assert_called_with(mock_comment.author,
                                                    mock_comment.body,
                                                    mock_comment.author_flair_css_class)

    def _assert_flair_not_added_to_author(self, mock_reddit_api):
        mock_subreddit = mock_reddit_api.subreddit.return_value
        assert mock_subreddit.flair.set.call_count == 0
