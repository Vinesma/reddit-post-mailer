""" Find the most upvoted reddit content in the last week and send an email with the contents.
    Uses `gpg` to decrypt the necessary files.
"""

import yagmail, subprocess, praw, os, argparse, logging

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
# GLOBALS
version = "1.0.0"
subreddit = "mealtimevideos"
min_post_score = 5
send_email = False
print_content = False

def loadArgs():
    """ Parse and load arguments.
    """
    global min_post_score
    global send_email
    global print_content
    global subreddit

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
        logging.basicConfig(level=logging.DEBUG, format="%(levelname)s : [%(funcName)s] %(message)s")
    else:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s : [%(funcName)s] %(message)s")

    if args.email:
        send_email = True

    if args.output:
        print_content = True

    if args.minscore is not None:
        min_post_score = args.minscore

    subreddit = args.subreddit

    logging.debug(f"Print to stdout: {print_content}")
    logging.debug(f"Send email: {send_email}")
    logging.debug(f"Min score for submissions: {min_post_score}")
    logging.debug(f"Subreddit: r/{subreddit}")

def gpgIsFound():
    """ A few checks to see if all necessary gpg files are present.
    """
    necessary_paths = ["/usr/bin/gpg", email_password_path, reddit_password_path, reddit_client_id_path, reddit_client_secret_path]
    notFound = False

    for path in necessary_paths:
        if not os.path.exists(path):
            logging.error(f"Path to {path} not found, it's necessary that a valid file is present there.")
            notFound = True

    if notFound:
        return False

    return True

def formatEmailContent(posts):
    """ Format the contents that will be sent as an email.
    """
    email_content = []
    for post in posts:
        title = f"<h5>{post['score']} Upvotes - <a href={post['url']}>{post['title']}</a></h5>"
        link  = f"<a href={post['url']}>{post['url']}</a>"
        html  = f"<div>{title}{link}</div>"

        email_content.append(html)
        email_content.append("<br>")

    return email_content

def sendMail(posts):
    """ Send an email using yagmail.
    """
    email_password = subprocess.getoutput(email_password_command)
    subject = f"The best {len(posts)} posts from r/{subreddit}!"
    body = formatEmailContent(posts)

    yag = yagmail.SMTP("otaviocos14@gmail.com", email_password)

    yag.send(subject=subject, contents=body)
    print("Mail sent.")

def fetchPosts():
    """ Fetch reddit submissions from a subreddit using praw.
    """
    reddit_password = subprocess.getoutput(reddit_password_command)
    reddit_client_id = subprocess.getoutput(reddit_client_id_command)
    reddit_client_secret = subprocess.getoutput(reddit_client_secret_command)

    reddit = praw.Reddit(client_id=reddit_client_id, client_secret=reddit_client_secret,
            password=reddit_password, user_agent=f"linux:reddit-picker:v{version} (by /u/Vinesma)",
            username="Vinesma")

    subreddit_name = reddit.subreddit(subreddit)
    subreddit_posts_iterable = subreddit_name.new(limit=150)
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

    logging.debug(f"Found {len(subreddit_posts)} suitable posts.")

    return subreddit_posts

def filterPosts(posts):
    """ Take the average score of all submissions and remove posts that fall below the threshold.
        Also sorts by upvotes.
    """
    scores = []
    for post in posts:
        scores.append(post['score'])

    avg_score = sum(scores) / len(scores)
    logging.debug(f"Calculated average score is {avg_score}")

    # Filter out posts lesser than the threshold.
    filtered_posts = filter(lambda post: post['score'] > avg_score, posts)
    filtered_posts = list(filtered_posts)

    # Sort list by upvotes.
    filtered_posts.sort(key=lambda post: post['score'], reverse=True)

    return filtered_posts

def printPosts(posts):
    """ Prints submissions to stdout.
    """
    logging.debug(f"Printing {len(posts)} selected posts.")

    for post in posts:
        print(f"^{post['score']} : {post['title']}\n{post['url']}")

def main():
    loadArgs()
    if gpgIsFound():
        posts = fetchPosts()
        posts = filterPosts(posts)

        if print_content:
            printPosts(posts)

        if send_email:
            sendMail(posts)
    else:
        logging.error(f"You need gpg installed in your system and all files required for this script to work!")

main()
