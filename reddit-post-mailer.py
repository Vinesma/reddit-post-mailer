""" Find the most upvoted reddit posts and send an email with the contents.
    Uses `gpg` to decrypt the necessary files.
"""

import yagmail, subprocess, os, argparse, logging, time, json, requests, math, sys

# PATHS
user_path = os.path.expanduser("~")
email_password_path = f"{user_path}/.neomutt/account.gpg"
# COMMANDS
decrypt_command="gpg --batch -q --decrypt"
email_password_command = f"{decrypt_command} {email_password_path}"
# GLOBALS
version = "1.2.1"
subreddit = "mealtimevideos"
num_fetched_posts = 150
min_post_score = 5
lower_limit = 3
reddit_retrieve_limit = 100
epoch = 0
send_email = False
print_content = False
print_links = False
use_epoch = False

def loadArgs():
    """ Parse and load arguments.
    """
    global num_fetched_posts
    global min_post_score
    global send_email
    global print_content
    global print_links
    global use_epoch
    global subreddit

    # Initializer
    parser = argparse.ArgumentParser(description="Find the most upvoted submissions to a subreddit and email them to the user.")
    # Argument definition
    # optional
    parser.add_argument("-v", "--verbose", help="make the application more verbose.", action="store_true")
    parser.add_argument("-e", "--email", help="send an email to the user with the selected post contents.", action="store_true")
    parser.add_argument("-o", "--output", help="print selected posts to stdout.", action="store_true")
    parser.add_argument("-u", "--urls", help="print just the links to stdout. Only works when used with --output", action="store_true")
    parser.add_argument("-a", "--afterutc", help="only retrieve posts from after the last run.", action="store_true")
    parser.add_argument("-m", "--minscore", type=int, help=f"the minimum amount of score a post needs to be selected initially. Default = {min_post_score}")
    parser.add_argument("-n", "--numfetch", type=int, help=f"how many posts to fetch from reddit. Default = {num_fetched_posts}")
    # positional
    parser.add_argument("subreddit", help="subreddit to select the posts from, 'r/' is not necessary.")
    args = parser.parse_args()

    # Loads arguments
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: [%(funcName)s] %(message)s")
    else:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s: [%(funcName)s] %(message)s")

    if args.email:
        send_email = True

    if args.afterutc:
        use_epoch = True

    if args.output:
        print_content = True
        if args.urls:
            print_links = True

    if args.minscore is not None:
        min_post_score = args.minscore

    if args.numfetch is not None:
        num_fetched_posts = args.numfetch

    subreddit = args.subreddit

    logging.debug(f"Print to stdout: {print_content}")
    logging.debug(f"Print links only: {print_links}")
    logging.debug(f"Send email: {send_email}")
    logging.debug(f"Number of posts to fetch from reddit: {num_fetched_posts}")
    logging.debug(f"Minimum score for submissions: {min_post_score}")
    logging.debug(f"Subreddit: r/{subreddit}")

def loadLastDate():
    """ Load the last date the program was ran.
    """
    global epoch

    if os.path.isfile("cache.json"):
        logging.debug("Save found.")
        with open("cache.json", "r") as cacheFile:
            epoch = json.load(cacheFile)
        logging.debug(f"Epoch is now: {epoch}")

def saveDate():
    """ Save the current epoch (to a file)
    """
    global epoch
    epoch = time.time()

    with open("cache.json", "w") as cacheFile:
        cacheFile.write(json.dumps(epoch))

    logging.debug("Save successful.")

def gpgIsFound():
    """ A few checks to see if all necessary gpg files are present.
    """
    necessary_paths = ["/usr/bin/gpg", email_password_path]

    for path in necessary_paths:
        if not os.path.exists(path):
            logging.error(f"Path to {path} not found, it's necessary that a valid file is present there.")
            return False

    return True

def formatEmailContent(posts):
    """ Format the contents that will be sent as an email.
    """
    email_content = []
    for post in posts:
        title = f"<h5>{post['score']} upvotes - <a href={post['url']}>{post['title']}</a></h5>"
        link  = f"<a href={post['url']}>{post['url']}</a>"
        comments = f"<a href={post['permalink']}>{post['comment_quantity']} comments</a>"

        html  = f"<div>{title}<ul><li>{link}</li><li>{comments}</li></ul></div>"

        email_content.append(html)
        email_content.append("<br>")

    return email_content

def sendMail(posts):
    """ Send an email using yagmail.
    """
    email_password = subprocess.getoutput(email_password_command)

    if use_epoch:
        epoch_human_readable = time.localtime(epoch)
        year, month, day = epoch_human_readable[:3]
        subject = f"The best {len(posts)} posts from r/{subreddit} since {day}/{month}/{year}!"
    else:
        subject = f"The best {len(posts)} posts from r/{subreddit}!"
    body = formatEmailContent(posts)

    yag = yagmail.SMTP("otaviocos14@gmail.com", email_password)

    yag.send(subject=subject, contents=body)
    print("Mail sent.")

def fetchPosts():
    """ Fetch reddit submissions from a subreddit.
    """
    if num_fetched_posts > reddit_retrieve_limit:
        num_requests = math.ceil(num_fetched_posts / reddit_retrieve_limit)
        num_fetched_posts_last = num_fetched_posts % 100
    else:
        num_requests = 1

    logging.debug(f"Calculated the need for {num_requests} requests to satisfy post amount.")
    count_requests = 0
    subreddit_posts = []
    after = ""

    while count_requests < num_requests:
        logging.debug(f"Making request {count_requests + 1}")
        headers = {'Host': 'www.reddit.com', 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:84.0) Gecko/20100101 Firefox/84.0'}

        if count_requests == 0:
            response = requests.get(f"https://www.reddit.com/r/{subreddit}/.json?limit=100", headers=headers)
        elif count_requests == num_requests - 1 and num_fetched_posts_last != 0:
            logging.debug(f"Last request reached, only fetching {num_fetched_posts_last} posts")
            response = requests.get(f"https://www.reddit.com/r/{subreddit}/.json?limit={num_fetched_posts_last}&after={after}", headers=headers)
        else:
            response = requests.get(f"https://www.reddit.com/r/{subreddit}/.json?limit=100&after={after}", headers=headers)

        response.raise_for_status()
        response = response.json()

        posts = response['data']['children']
        for post in posts:
            post_info = post['data']
            new_post = {
                    "id": post_info['id'], "title": post_info['title'],
                    "score": post_info['score'],
                    "comment_quantity": post_info['num_comments'], "permalink": f"https://www.reddit.com{post_info['permalink']}",
                    "utc": post_info['created_utc'],
                    "url": post_info['url']
                    }
            # Filter really low quality posts
            if new_post['score'] >= min_post_score:
                subreddit_posts.append(new_post)

        after = response['data']['after']
        count_requests += 1

    logging.debug(f"Found {len(subreddit_posts)} suitable posts.")
    return subreddit_posts

def filterPosts(posts):
    """ Take the average score of all submissions and remove posts that fall below the threshold.
        Can filter older posts.
        Finally, it sorts by upvotes.
    """
    scores = []
    for post in posts:
        scores.append(post['score'])

    avg_score = sum(scores) / len(scores)
    logging.debug(f"Calculated average score is {avg_score}")

    # Filter out posts lesser than the threshold.
    filtered_posts = filter(lambda post: post['score'] > avg_score, posts)
    filtered_posts = list(filtered_posts)

    if use_epoch:
        # Filter out posts older than current epoch.
        filtered_posts = filter(lambda post: post['utc'] > epoch, filtered_posts)
        filtered_posts = list(filtered_posts)

    # Sort list by upvotes.
    filtered_posts.sort(key=lambda post: post['score'], reverse=True)

    return filtered_posts

def printPosts(posts):
    """ Prints submissions to stdout.
    """
    logging.debug(f"Printing {len(posts)} selected posts.")

    for post in posts:
        if not print_links:
            print(f"^{post['score']} : {post['title']}\n{post['url']}")
        else:
            print(f"{post['url']}")

def main():
    loadArgs()

    if num_fetched_posts > 999:
        print("Too many posts to retrieve, only values less than 1000 are supported.")
        sys.exit(1)

    if use_epoch:
        loadLastDate()

    if gpgIsFound():
        posts = fetchPosts()
        posts = filterPosts(posts)

        # Do not return anything if fewer posts than {lower_limit} are found.
        if len(posts) > lower_limit:
            if print_content:
                printPosts(posts)

            if send_email:
                sendMail(posts)

            if use_epoch:
                saveDate()
        else:
            print("Nothing to do. Not enough posts retrieved.")
    else:
        logging.error(f"You need gpg installed in your system and all files required for this script to work!")

main()
