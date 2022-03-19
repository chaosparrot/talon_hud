from .typing import HudContentEvent, CLAIM_WIDGET_TOPIC_TYPE, CLAIM_BROADCAST
from typing import Any
import copy


# Class for managing a part of the HUD content
class HudPartialContent:

    topic_types = None
    persisted_topics = None
	
    def __init__(self, topic_types = []):
        self.persisted_topics = []
        self.topic_types = {}
        for topic_type in topic_types:
            self.topic_types[topic_type] = {}

    def set_persisted_topics(self, topics: list[str]):
        self.persisted_topics = copy.copy(topics)

    # Get a specific topic from the known topic types in the order of creation
    def get_topic(self, topic_type: str, topic = None) -> list:
        topic_contents = []
        if topic_type in self.topic_types:
            for ordered_topic in self.persisted_topics:
                if ordered_topic in self.topic_types[topic_type] and ( topic == None or topic == ordered_topic ):
                    if isinstance(self.topic_types[topic_type][ordered_topic], list):
                        topic_contents.extend(self.topic_types[topic_type][ordered_topic])
                    else:
                        topic_contents.append(self.topic_types[topic_type][ordered_topic])

        return topic_contents

    def get_variable(self, topic:str, default: Any) -> Any:
        if "variable" in self.topic_types and topic in self.topic_types["variable"]:
            return self.topic_types["variable"][topic]
        else:
            return default

    # Override a specific topic from the known topic types
    def set_topic(self, topic_type, topic, content, claim_type = CLAIM_BROADCAST):
        if topic_type not in self.topic_types:
            self.topic_types[topic_type] = {}
        
        # Clear the topic type if it is given
        if claim_type == CLAIM_WIDGET_TOPIC_TYPE:
            current_topics = list(self.topic_types[topic_type].keys())
            for current_topic in current_topics:
                if current_topic != topic:
                    self.remove_topic(topic_type, current_topic)

        self.topic_types[topic_type][topic] = content
        if topic_type != "variable" and topic not in self.persisted_topics:
            self.persisted_topics.append(topic)

    # Remove a specific topic
    def remove_topic(self, topic_type, topic):
        if topic_type not in self.topic_types:
            self.topic_types[topic_type] = {}

        # Make sure the persisted topics are altered only when the actual topic is removed
        # To properly ensure the topics survive a full reload where content is publishing continuously
        if topic in self.persisted_topics:
            self.persisted_topics.remove(topic)

        if topic in self.topic_types[topic_type]:
            del self.topic_types[topic_type][topic]

    # Get a unique list of all the current topics on the widget
    def get_current_topics(self):
        return copy.copy(self.persisted_topics)

    # Process an event
    def process_event(self, event: HudContentEvent):
        if event.operation == "replace":
            self.set_topic(event.topic_type, event.topic, event.content, event.claim)
        elif event.operation == "remove":
            self.remove_topic(event.topic_type, event.topic)
        elif event.operation == "dump":
            for topic_type in event.content["topic_types"]:
                if topic_type not in self.topic_types:
                    continue
                for topic in event.content["topic_types"][topic_type]:
                    if topic in self.persisted_topics:
                        self.set_topic(topic_type, topic, event.content["topic_types"][topic_type][topic])
        # Other types of content events need manual changing ( patch and append for example )
