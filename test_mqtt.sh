#!/bin/bash

source .env

mqtt_broker="localhost"
root_topic="ragpipes"
chat_node="default"
sleep_delay=5

function pub {
    mosquitto_pub -h ${mqtt_broker} -t "$1" -m "$2"
}

function wait_for_key {
    read -p "Press enter to continue"
}


echo "Chat: Test RAG"
pub "${root_topic}/chat/${chat_node}/command" '{ "options": { "query": "What is Janes favourite food" } }'
wait_for_key

echo "Wikipedia: Football"
pub "${root_topic}/loader/wikipedia/command" '{ "options": { "query": "Football" } }'
wait_for_key

echo "Wikipedia: Commodore Amiga"
pub "${root_topic}/loader/wikipedia/command" '{ "options": { "query": "Commodore Amiga" } }'
wait_for_key

echo "Website: ipnt.uk"
pub "${root_topic}/loader/web/command" '{ "options": { "url": "https://ipnt.uk" } }'
wait_for_key

echo "Text: Janes Diet"
pub "${root_topic}/loader/text/command" '{ "options": { "text": "Janes favourite food is Spaghetti and Meatballs." } }'
wait_for_key

echo "Text: Joes Diet"
pub "${root_topic}/loader/text/command" '{ "options": { "text": "Joes favourite food is Burger and Fries." } }'
wait_for_key

echo "Chat: Test RAG Again"
pub "${root_topic}/chat/${chat_node}/command" '{ "options": { "query": "What is Janes favourite food" } }'
wait_for_key
