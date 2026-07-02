# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

My initial UML design contain main classes including pet care Tasks and Scheduler. These are the necessary basic classes or actions that the design needs to incorporate. Some other classes that will be needed include Owner and Pet so that the app will allow a user to input their personal information and their pet's information. 

The Pet class will contain information about the pet and the User class will contain information about the user. The Tasks class will take care of the necessary tasks the user would need to complete and track including walking, feeding, meds, enrichment, and groooming (these might be enums or examples of classes needed). The Scheduler class will contain subclasses including time availability (weekdays)Schedule to produce a daily plan.

Main Objects: Owner, Pet, Task, Scheduler
Owner - 
    Attributes: name, age, gender, location, how long user has owned pet, 

    Methods: owns pets, completes tasks, has time availability, has priority for what tasks or times, edit tasks, add tasks, remove tasks, remove pet, add pet, use scheduler to generate tasks daily
Pet - 
    Attributes: type of animal, preference of time for doing a task, needed meds, 
    
    Methods: do a task
Tasks - 
    Attributes: type of task (walks, feeding, meds, enrichment, grooming, etc.), how long for each task (duration), when would these tasks need to be done, owner preference for which tasks, whether a task is completed or not, priority for a task

    Methods: check off completion, check owner preference

Scheduler - 
    Attributes: days of the week, what tasks for what pet daily, 

    Methods: create a schedule of daily tasks for each pet, explain why the plan was chosen, track what tasks are completed and incomplete, track how long it takes to complete a task

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

Claude AI noted some main gaps between Task, Owner, and Pet but there is no clear ownership link between the three and the same task could exist in multiple places. The model does not define who owns a task so methods like complete, scheduling and preference matching will become ambiguous. The scheduler also only builds schedules for the first day and does not account for multiuple pets, days or time conflicts. 

Some bottlenecks to consider are also to due_time is stored as a string which can be messy if we have more realistic formats for times like 10AM or 10:30AM. 

One change that needs to be added is to state relationships explicitly such as for each Task, which owner or pet should it belong to. Each owner should manage its own tasks and each pet should manage its care needs. 

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

Constraints that needed to be considered include time and priority of each task. The constraints that mattered the most are the ones that the scheduler needed to have to be able to generate the schedule. For example, owner pet time of day preference is needed to match so that we could resolve any scheduling conflicts as well. 

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

One tradeoff is that the scheudler builds the week as a repeating pattern rather than real calendar dates so it just copies the daily task into one of the 7-day slots without actually knowing today's date, tomorrow's date and so on. It isn't accounting for specific dates like holidays like July 4th where the tasks could change or be lighter for the day. Thus we would need the separate helper function (tasks_due_on) to check that each task's actual due date is direct. The trade off is we have less code and it's easier to reason but the cost of the schedule being a typical week simulation rather than an actual accurate calendar.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

I used Claude to help me with all the above inlcudin gdesing, brainstorming, debugging, refactoring, and testing. The prompts that were helpful were the ones that were specific and gave examples to describe what is expected of the task. Using separate chat sessions help me be able to focus and revisit prompts as well as tasks I have asked it to do. It helps prevent repetition unintentionally.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

I did not acccept the AI's suggestion when it didnt make sense to me or if it misunderstood what I wanted it to do. For example, when it didn't include some of the specific methods I wanted it to include, I had to manually tell them that I want to include such methods since it did not consider them.
---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

I tested sorting, as well as basic behaviuors like flipping if a task is completed or if tasks are repeated. Edge cases are important to tests as well as functionality since it could break the app and ruin the user experience. 

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

I am fairly confident the schedueler works correctly and if I had more time, I would include testing if we combine tasks for multiple days like a Monday to Wednesday task. This is more realistic to think about. Another would be considering the removal of the pet or the task in testing.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

I am most satisfied with the functionality of the app and how much more detailed it is than how it started. I learned a bit about Streamlit as well and it was cool to see how the code affects the UI a bit.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

I would improve to make it more UI friendly like allowing the user to check off the tasks for the day and let it update in real time. 

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

One important takeaway is that when working with AI, we need to think of edge cases and test thoroughly as there could be human decisions that the AI would not have thought of since it could be generalizing rather than think of specific cases. It is necessary to look at what the AI is adding to make it make sense to you.
