# How Our Notification System Works

This document explains the architecture of our real-time notification system in simple terms, so anyone—technical or non-technical—can understand how it works!

---

## 1. The Old Way: "Are we there yet?" (Polling & Direct Calling)

Imagine a restaurant where customers are waiting for their food.

In the old system, two inefficient things were happening:
1. **The Chef's Distraction (Direct Calling):** Whenever the Chef (the **Ticket Service**) finished a meal, they had to stop cooking, walk out to the dining room, find the specific Waiter (the **Notification Service**), and say, *"Hey, deliver this!"* This forced the Chef to know the Waiters and do extra work outside of cooking.
2. **The Annoying Customer (Polling):** Meanwhile, the customer (the **Frontend Dashboard**) was extremely impatient. Every 5 seconds, they would walk up to the kitchen window and ask, *"Is my notification ready? How about now? Now?"* This wasted a lot of energy and cost a lot of money (server resources).

---

## 2. The New Way: The Bell and The Tube (Event Bus & SSE)

We rebuilt the system to be much faster, cheaper, and more organized. Here is how it works now:

### Step 1: The Event Bus (The Kitchen Bell)
Now, the Chef (Ticket Service) never leaves the kitchen. When a user creates a new ticket, the Chef simply finishes the task, puts it on the counter, and **rings a bell** (publishes an event: `"ticket-created"`).

The Chef immediately goes back to work. They don't know who the Waiters are, and they don't care. 

This bell system is our **Event Bus**. It allows different parts of our app to say *"Hey, something happened!"* without having to hunt down the specific person who needs to know.

### Step 2: The Notification Service (The Waiter)
The Waiter (Notification Service) is simply listening for the bell. As soon as they hear the `"ticket-created"` bell, they grab the details and prepare the notification for the customer. 

Because of the Event Bus, the Waiter and the Chef are completely independent (what developers call **"Loose Coupling"**). 

### Step 3: Server-Sent Events (The Delivery Tube)
We fixed the impatient customer problem by installing a direct delivery tube straight to each customer's table. 

When a user logs into the app, we connect a specialized tube (an **SSE Connection**) from the server to their screen. 
- The customer no longer has to ask *"Is it ready?"* every 5 seconds (no more polling!).
- They just sit back and wait.
- When the Waiter (Notification Service) has a notification for **User #10**, they drop it down User #10's specific tube. It arrives instantly on their screen.

---

## 3. A Real-World Example (Admin Replies to a Ticket)

Here is exactly what happens in our codebase when an Admin replies to a user's ticket:

1. **Admin Clicks Reply:** The Admin submits a reply on the frontend.
2. **Ticket Service:** Our backend saves the reply to the PostgreSQL database.
3. **The Bell Rings:** The Ticket Service shouts out to the Event Bus: *"Hey everyone, a ticket was replied to!"* (`event_bus.publish("ticket-replied")`).
4. **The Listener:** The Notification Service, which is always listening, hears the event. It saves a new notification in the database.
5. **The Tube:** The Notification Service checks its switchboard, finds the specific SSE tube connected to the user who owns that ticket, and pushes the data down that single tube.
6. **Instant Delivery:** The user sees a pop-up on their screen in milliseconds, while using zero extra database queries or polling resources! 
