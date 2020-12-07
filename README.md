# reddit-post-mailer
Selects the most upvoted subreddit posts on average and sends them to the user via gmail SMTP.

### How it works

The script uses gpg to decrypt the user's gmail password, reddit password, reddit client ID and reddit client secret.

Using this data, it can connect to reddit, fetch posts from the subreddit specified by the user, filter them down and then output and/or email the contents.

If running the script as a cron job the user can also try using the `--afterutc` flag so that the script never fetches older submissions.

### How to use

Pass the `--help` flag to the script to learn all the possible options.

### Dependencies

`yagmail` for email support and `praw` for fetching reddit submissions.
