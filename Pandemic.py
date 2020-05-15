import glob
import os
from os import path
from instaloader import Instaloader, Profile, Post
import datetime
import lzma
import json
import networkx as nx
import matplotlib.pyplot as plt

loader = Instaloader()
NUM_POSTS = 10
MAX_DAYS = 14
LIKES_WEIGHT = 1
COMMENTS_WEIGHT = 1
NUM_FOLLOWERS_WEIGHT = 1
NUM_POSTS_WEIGHT = 1
tagged_per_day = {}
ALL_USERS_TAGGED = []
CLOSED = []
NODES = []
EDGES = []
NUMBERED_USERS = {}

#get all tagged users that apeared in the users posts in the last X days
def get_tagged_users_per_each_post(USER):
    user_profile = Profile.from_username(loader.context, USER)
    posts = get_recent_posts(user_profile)
    tags_per_post = []
    for post in posts:
        tagged = post.tagged_users
        print(tagged)
        print("Location: {}".format(post.location))
        tags_per_post.append(tagged)
    print("All users per tag: {}".format(tags_per_post))

def get_user_summary(users):
    count = 0
    ###NOTE THE CHANGE HERE
    tagged = []
    for tag in tagged:
        profile = Profile.from_username(loader.context, tag)
        if profile.username not in users:
            summary = get_summary(profile)
            users[profile.username] = summary
            count += 1
            print('{}: {}'.format(count, profile.username))
            if count == NUM_POSTS:
                break
    return users


def get_summary(profile):
    user = {}
    current_date = datetime.datetime.now()
    for post in profile.get_posts():
        delta = current_date - post.date
        if (delta.days > MAX_DAYS):
            break
    return user

#This function gets a list of posts and sorts them by day of the post
def sort_posts_by_day(posts):
    date_list = []
    sorted_posts = {}
    #get a list of all dates
    for post in posts:
        day = post.date.day
        month = post.date.month
        year = post.date.year
        post_date = "{}.{}.{}".format(day, month, year)
        if post_date in date_list:
            continue
        else:
            date_list.append(post_date)
    for post in posts:
        day = post.date.day
        month = post.date.month
        year = post.date.year
        post_date = "{}.{}.{}".format(day, month, year)
        if post_date in date_list:
            if sorted_posts.__contains__(post_date):
                sorted_posts[post_date].append(post)
            else:
                sorted_posts[post_date] = [post]
    return sorted_posts, date_list

#get all post from X recent days (MAX_DAYS)
def get_recent_posts(profile):
    current_date = datetime.datetime.now()
    relevant_posts = []
    all_posts = profile.get_posts()

    #sorted_posts = sort_posts_by_day(all_posts)
    for post in all_posts:
        delta = current_date - post.date
        if (delta.days > MAX_DAYS):
            break
        relevant_posts.append(post)
    return relevant_posts

#Check if the user isnt in the tagged list yet and wasnt sent to the main function yet, and adds it to the tagged list
def add_to_all_users_list(user):
    if user not in ALL_USERS_TAGGED and user not in CLOSED:
        ALL_USERS_TAGGED.append(user)


#get a list of all tagged users in each post over X period of time
def get_all_tagged_users_in_posts_per_day(USER):
    #add node to closed list
    CLOSED.append(USER)
    add_to_numbered_users(USER)
    #get the user profile by its username
    user_profile = Profile.from_username(loader.context, USER)
    #get all post taggers that a specific user was tagged in
    taggers = get_taggers_from_json(USER)
    #add all taggers to the open list
    for t in taggers:
        add_to_all_users_list(t)
    #get posts from X last days
    posts = get_recent_posts(user_profile)
    #sort the posts according to their dates
    posts_dic, date_list = sort_posts_by_day(posts)

    for date in (posts_dic):
        tagged = []
        for post in posts_dic[date]:
            user = post.tagged_users
            for u in user:
                add_to_numbered_users(u)
                add_to_all_users_list(u)
                if u not in tagged:
                    edge = (NUMBERED_USERS[USER], NUMBERED_USERS[u], date)
                    EDGES.append(edge)
                    tagged.append(u)
        #summary = get_user_summary(users)
        #check if the date is already a key in the list
        if tagged_per_day.__contains__(date):
            tagged_per_day[date].append(tagged)
            #OPTIONAL - IF YOU WANT ALL TAGGERS TO APPEAR IN FINAL LIST.
            tagged_per_day[date].append(USER)
        #date is a new date to insert
        else:
            tagged_per_day[date] = [tagged]
    #recursion condition - continue as long as there is a user that wasnt passed on to the function  yet.
    while ALL_USERS_TAGGED.__len__() > 0:
        get_all_tagged_users_in_posts_per_day(ALL_USERS_TAGGED.pop())

def add_to_numbered_users(user):
    if user not in NUMBERED_USERS:
       NUMBERED_USERS[user] = NUMBERED_USERS.__len__()+1

#print the dictionary of the tagged users
def print_tagged_dic(tagged_per_day):
    for day in tagged_per_day:
        print("Day {} - tagged: {}".format(day, tagged_per_day[day]))
#this downloads all of the posts that a specific username was tagged in
def get_all_tagged_posts_by_user(user):
    user_profile = Profile.from_username(loader.context, user)
    loader.download_tagged(user_profile)

#this function extracts all the json files
def get_jsons(user):
    files = []
    user_json_string = "{}﹨꞉tagged/".format(user)
    if path.exists(user_json_string):
        os.chdir(user_json_string)
        for file in glob.glob("*.json.xz"):
            files.append(user_json_string + file)
        os.chdir('..')
    return files

#this function gets the usernames of all the post owners = taggers
def get_taggers_from_json(user):
    get_all_tagged_posts_by_user(user)
    files = get_jsons(user)
    taggers = []
    for f in files:
        jsonfile = lzma.open(f)
        data = json.load(jsonfile)
        node = data['node']
        owner = node['owner']
        username = owner['username']# get the username
        taggers.append(username)
    return taggers

#This function saves and plots the network, represented as a multi bidirectional graph
def plot_results(edges):
    final = []
    dic = {}
    for j, i in enumerate(edges):
        edge = [edges[j][0], edges[j][1]]
        dicedge = (edges[j][0], edges[j][1])
        final.append(edge)
        dic[dicedge] = (edges[j][2])
    G = nx.MultiDiGraph()
    G.add_edges_from(final)
    pos = nx.spring_layout(G)
    plt.figure()
    nx.draw(G, pos, edge_color='black', width=1, linewidths=1,
            node_size=500, node_color='red', alpha=0.9,
            labels={node: node for node in G.nodes()})
    nx.draw_networkx_edge_labels(G, pos, edge_labels=dic, font_color='blue')
    plt.axis('off')
    plt.savefig('Network_Graph.png')
    plt.show()

if __name__ == "__main__":
    USER = "instapandemic1"
    PASSWORD = "instapandemic"
    loader.login(USER, PASSWORD)
    #get_tagged_users_per_each_post(USER)
    get_all_tagged_users_in_posts_per_day(USER)
    #print_tagged_dic(tagged_per_day)
    graph_table = {v: k for k, v in NUMBERED_USERS.items()}
    print(graph_table)
    plot_results(EDGES)



# instapandemic1 instapandemic
# instapandemic2 instapandemic
# instademic3 mDZBL5xTSzzFfk8
# instademic4 dfgdfgd345#fdw345@#$DE
# instademic5 a9WDRVU3XtqshgG