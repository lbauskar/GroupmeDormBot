from gmbot import GMBot
from os import getenv


class LFBot(GMBot):
    """This bot is intended for use in the main dorm-wide chat."""
    ban_list = ["GroupMe"]

    def chat(self, data):
        if data["name"] != self.name and data["name"] not in self.ban_list:
            chat_input = str.lower(data["text"])
            if "@everyone" in chat_input and self.not_a_freshman(data):
                self.at_everyone()
            if "@freshmen" in chat_input and self.not_a_freshman(data):
                self.at_freshmen()
            if "!help" in chat_input:
                msg = "@{}, I know the following commands: !faq, !movein, !RAs, !launch," \
                      " !code, !core, !registration, !howdy, !g(oogle), @everyone, @freshmen".format(data["name"])
                self.send_message(msg, [self.create_mention(msg, data)])
            if "!faq" in chat_input:
                self.send_message(getenv("FAQ_URL"))
            if "!movein" in chat_input:
                self.send_message(getenv("MOVEIN_URL"))
            if "!launch" in chat_input:
                self.send_message(getenv("LAUNCH_URL"))
            if "!howdy" in chat_input:
                msg = "Howdy Week Schedule:"
                img_attachment = {
                    "type": "image",
                    "url": "https://i.groupme.com/844x1500.jpeg.4bf577afcfc2404eb55e1c7bcaa1e7c3"
                }
                self.send_message(msg, [img_attachment])
            if "!code" in chat_input:
                msg = "@{} my github repository (source code) can be found at " \
                      "https://github.com/lbauskar/GroupmeDormBot".format(data["name"])
                self.send_message(msg, [self.create_mention(msg, data)])
            if "!ras" in chat_input:
                self.send_message(getenv("RA_STR"))
            if "!core" in chat_input:
                self.send_message("core.tamu.edu\nicd.tamu.edu")
            if "!registration" in chat_input or "shut up" in chat_input:
                msg = "Yes, more seats will open for your classes. No we don't know when. " \
                      "Check your major's catalog for what classes to take."
                self.send_message(msg)
            if "!google " in chat_input:
                self.use_google(chat_input, command_used="!google ")
            elif "!g " in chat_input:
                self.use_google(chat_input, command_used="!g ")
            if "!muted" in chat_input:
                self.num_muted()

    def groupme_events(self, data):
        """Parse messages from GroupMe client."""
        greeting = getenv("LF_GROUP_NAME")

        def greet_joined_user():
            new_name = data["text"][0: data["text"].find("has joined") - 1]
            msg = greeting.format(new_name, getenv("LF_GROUP_NAME"))
            new_user = self.get_user_dict([new_name])
            if new_user:
                mention = {"type": "mentions", "user_ids": [new_user[new_name]],
                           "loci": [(msg.find("@"), len(new_name) + 1)]}
                self.send_message(msg, [mention])
            else:
                self.send_message(msg)

        def greet_added_users():
            def list_added_users():  # create list of new user names from "added" message
                names = data["text"][data["text"].find("added") + 6: data["text"].find("to the group") - 1].split(", ")
                if " and " in names[-1]:
                    last_users = names[-1].split(" and ")
                    names[-1] = last_users[0]
                    names += [last_users[1]]
                return names

            new_names = list_added_users()
            new_users = self.get_user_dict(new_names)
            for user, user_id in new_users:  # @ users who can be mentioned
                msg = greeting.format(user, getenv("LF_GROUP_NAME"))
                mention = {"type": "mentions", "user_ids": [user_id], "loci": [(msg.find("@"), len(user) + 1)]}
                self.send_message(msg, [mention])
                new_names.remove(user)
            for name in new_names:  # plain text for those who can't be mentioned
                msg = greeting.format(name)
                self.send_message(msg)

        if "has joined" in data["text"]:
            greet_joined_user()
        elif "added" in data["text"]:
            greet_added_users()

    def at_everyone(self):
        """Mention every member of a group."""
        for mention in self.create_multi_mention(self.get_member_list(), bold_location=(0, 8)):
            self.send_message("Everyone read the GroupMe!", [mention])

    def at_freshmen(self):
        """Mention every freshman in the group."""
        member_list = [member for member in self.get_member_list() if member["user_id"] not in self.get_a_team_ids()]
        if member_list:
            for mention in self.create_multi_mention(member_list, bold_location=(0, 8)):
                self.send_message("Freshmen, read the GroupMe pls", [mention])

    def get_a_team_ids(self):
        """Get the user ids of every non-freshman."""
        a_name_list = getenv("A_TEAM_LIST").split(", ")
        return [member["name"] for member in self.get_member_list() if member["name"] in a_name_list]

    def not_a_freshman(self, data):
        """See if user is not a freshman."""
        return data["user_id"] in self.get_a_team_ids()

    def use_google(self, text, command_used):
        """Create snide Google search from a message."""
        search_terms = text[text.find(command_used) + len(command_used):].split()
        if search_terms:
            if search_terms[0][0] == '"':
                for i, term in enumerate(search_terms):
                    if term[-1] == '"':
                        search_terms = search_terms[0:i+1]
                        break
            url = "http://letmegooglethat.com/?q="
            for term in search_terms:
                url += ''.join(ch for ch in term if ch.isalnum()) + "+"  # make term alphanumeric and add it to url
            url = url[:-1]
            if url[-1] != '=' and url[-1] != '+':  # if usable search terms were inputted
                self.send_message("use Google\n"+url)

    def num_muted(self):
        """find number of users who have muted the chat"""
        num_muted = 0
        list_len = 0
        for member in self.get_member_list():
            list_len += 1
            if member["muted"]:
                num_muted += 1
        percent_muted = round(num_muted/list_len * 100)
        self.send_message("{} users ({} percent) have this chat muted.".format(num_muted, percent_muted))