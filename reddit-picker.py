""" Find the most upvoted reddit content in the last week and send an email with the contents.
    Uses `gpg` to decrypt the necessary files.
"""

import yagmail, subprocess, praw, os, argparse

# PATHS
user_path = os.path.expanduser("~")
email_password_path = f"{user_path}/.neomutt/account.gpg"
reddit_password_path = f"{user_path}/.neomutt/reddit-pass.gpg"
reddit_client_id_path = f"{user_path}/.neomutt/reddit-client-id.gpg"
reddit_client_secret_path = f"{user_path}/.neomutt/reddit-client-secret.gpg"
# COMMANDS
decrypt_command="gpg --batch -q --decrypt"
email_password_command = f"{decrypt_command} {email_password_path}"
reddit_password_command = f"{decrypt_command} {reddit_password_path}"
reddit_client_id_command = f"{decrypt_command} {reddit_client_id_path}"
reddit_client_secret_command = f"{decrypt_command} {reddit_client_secret_path}"
# VARS
version = "0.0.1"
min_post_score = 5
send_email = False
print_content = True
verbose = False

def loadArgs():
    """ Parse and load arguments.
    """
    global min_post_score
    global send_email
    global print_content
    global verbose

    # Initializer
    parser = argparse.ArgumentParser(description="Find the most upvoted submissions to a subreddit and email them to the user.")
    # Argument definition
    # optional
    parser.add_argument("-v", "--verbose", help="Control amount of output.", action="store_true")
    parser.add_argument("-e", "--email", help="Send an email to the user with the selected post contents.", action="store_true")
    parser.add_argument("-o", "--output", help="Print selected posts to stdout.", action="store_true")
    parser.add_argument("-m", "--minscore", type=int, help="The minimum amount of score a post needs to be selected initially. Default = 5")
    # positional
    parser.add_argument("subreddit", help="Subreddit to select the posts from, 'r/' is not necessary.")
    args = parser.parse_args()

    # Loads arguments
    if args.verbose:
        verbose = True
    if args.email:
        send_email = True
    if args.output:
        print_content = True
    if args.minscore is not None:
        min_post_score = args.minscore

def gpgIsFound():
    """ A few checks to see if all necessary gpg files are present.
    """
    necessary_paths = ["/usr/bin/gpg", email_password_path, reddit_password_path, reddit_client_id_path, reddit_client_secret_path]
    notFound = False

    for path in necessary_paths:
        if not os.path.exists(path):
            print(f"Path to {path} not found, it's necessary that a valid file is present there.")
            notFound = True

    if notFound:
        return False

    return True

def formatEmailContent(posts):
    """ Format the contents that will be sent as an email.
    """
    #TODO
    pass

def sendMail():
    """ Send an email.
    """
    email_password = subprocess.getoutput(email_password_command)

    yag = yagmail.SMTP("otaviocos14@gmail.com", email_password)
    contents = ["This is the body", "Here is more text", "/home/vinesma/Music/HOME/The Moment Before.mp3"]
    yag.send("otaviocos14@gmail.com", "Test email", contents)

def fetchPosts(subreddit_name):
    """ Fetch reddit submissions from a subreddit using praw.
    """
    reddit_password = subprocess.getoutput(reddit_password_command)
    reddit_client_id = subprocess.getoutput(reddit_client_id_command)
    reddit_client_secret = subprocess.getoutput(reddit_client_secret_command)

    reddit = praw.Reddit(client_id=reddit_client_id, client_secret=reddit_client_secret,
            password=reddit_password, user_agent=f"linux:reddit-picker:v{version} (by /u/Vinesma)",
            username="Vinesma")

    subreddit = reddit.subreddit(subreddit_name)
    subreddit_posts_iterable = subreddit.new(limit=150)
    subreddit_posts = []

    for post in subreddit_posts_iterable:
        new_post = {
                "id": post.id, "title": post.title,
                "score": post.score, "comment_quantity": post.num_comments,
                "utc": post.created_utc,
                "url": post.url
                }
        # Filter really low quality posts
        if new_post['score'] >= min_post_score:
            subreddit_posts.append(new_post)

    return subreddit_posts

def filterPosts(posts):
    """ Take the average score of all submissions and remove posts that fall below the threshold.
    """
    scores = []
    for post in posts:
        scores.append(post['score'])

    avg_score = sum(scores) / len(scores)
    print(f"Calculated score average is {avg_score}")

    filtered_posts = list(filter(lambda post: post['score'] > avg_score, posts))

    return filtered_posts

def printPosts(posts):
    """ Prints submissions to stdout.
    """
    for post in posts:
        print(f"{post['score']} : {post['title']}\n{post['url']}")

def main():
    if gpgIsFound():
        posts = fetchPosts("mealtimevideos")
        posts = filterPosts(posts)
        printPosts(posts)
        # sendMail()
    else:
        print(f"You need gpg installed in your system and all files required for this script to work!")

main()
