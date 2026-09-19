i am building a  restaurant order mangagament ai agent using langgraph.

I will give you clear explaination about my project and idea and what is the architecture of project. I will also explain you nodes the state and the edges. In the end i will also provide you with test case scenarios to simulate and tell me whether it pass or not

the rough plan is as follow:
## GIVING ORDER
there will be a user . when the code runs it will take an order from user , it will be taken as input and user will type it .
this order should go to llm .order should contain dish name and quantity . For simplicity purpose as of now we will limit the order to a one particualar dish and as many quantity user wants. The llm will extract dish name and quantity from the input . 
If the user input is unrelated to food ordering llm should not process that request and tell user that it is a food ordering agent not a general llm.

## CONFIRMING ORDER
Once the llm has order dish and quantity it will send it to a node ORDER_CONFIRMED
the task of this order confirm is to check for the menu(i will tell you meny later in this prompt)
then this node will decide one of 3 case
order is confirmed
order is partially available( means quantity not sufficient )
order is not available(means dish is not in menu or 0 quantity available) 
it will put this in the status of state( i will tell you the exact content of langgraph state as well)

once the llm recieve order is confirmed it should call another node call COOK
if the llm recieve order to be partially confirmed it should again prompt the user to decide whether to continue with the available quantity or place order again. 
This order retries is limited to 3 attempts, if in 3 attempt the user is not satisfied the system will come to END node
if the llm recieve order not available it should prompt user to decide any other dish. The order retry is limit to 3 attempts . If after 3 attempts the user is not satisfies the system will come to END node

## COOK
now when the COOK node is called
there can be 2 cases
order is ready and status id READY
cook fails order is not ready ( we can use a prov func). give 40% chance of fail and 60& chance of success. 
if cook fails there should be 1 more attempt to allow cook to succes if it fails again then llm should issue a apology to user and come to END node

if the cook succedd then the status will be ready
and node will be called which is SERVE

## SERVE
in SERVE THERE ARE ALSO 2 CASES
serve pass
serve fails . it also have 2 fail attempts if it fails in both then the llm should issue an apology to user and come to END node

if it suceed the status will become complete the llm should issue a message to the user saying your order is complete

if the serve fails then the cook should be called and if the cook is exhauseted by its retrying attempts then it will issue and apoplogy to user saying order is cancelled  and come to END state

## LANGGRAPH
 now the state of langgraph
there should be a annotated message between llm and user
there should be order details
required quantity as int
dish name as str
available quantity as int
order confirm will write the available quantity by reading menu
the llm should should get to know the order confirm status by reading its state
if a dish not available in the menu then the oder confirm should write 0 as avail quantity

there should be a status
each node will update status as per the above rules
order retry attempts shoudl be 3
cook retry attempts shoul be 2
delivery retry attempts should be 2
each time a failure happen and the node is retrying it should decrement the counter if any retry becomes 0 it means it is over. llm should understand whether it has to give a retry or issue apology by reading this counter.
in the end there should be final  result whether the order was complete or not

write the code and ask if there are any open qusetions from your side then ask i will give you some test scenarios to test later on


## TEST CASE SCENARIOS
test case 1
a user ask a unrelated question
then he place a order which is partial and wants to order again
again he orders a dish which is not available
excpected: end due to order retry are complete

test case2
user places a order which is available
order is confirmed
cook gain success
served fail once
cook retries success
serve does success

test case 3
user order partial 
does not partial
order gain full available
order confirmed
cook fail
cook retry
cook success
serve fail 
cook retry success
serve fail again
cook does not retry due to  retry exhaust
overall FAIL

