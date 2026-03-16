I'm building an AI chat app in `PyQt6`. The window in which the chat happens is my
`PiecesWindow()`. 
Here is a part of its constructor:

```python
class PiecesWindow(...):
    def __init__(self, ...) -> None:
        ...
        self.__bubble_frames:list[qt.QTextFrame] = []
        self.__conversation_input: Optional[gui.templates.textmanipulation.InputEditor] = None
        self.__conversation_console: Optional[gui.templates.textmanipulation.ConsoleDisplay] = None
        ...
        return
```

The user can type his  messages in `self.__conversation_input` which is of type `InputEditor` (a
subclass from `QTextEdit`).

The chat interaction (both user messages and AI replies) are shown as "text bubbles" in
`self.__conversation_console`, which is of type `ConsoleDisplay` (a subclass from `QTextBrowser`).
Every "text bubble" is in fact a `QTextFrame()`-instance. I keep a list to those "text bubbles" in
the variable `self.__bubble_frames`.

Here is the method that inserts a text bubble into `self.__conversation_console`:

```python
    def insert_bubble(self,
                      html_snippet: str,
                      background_color: str = "#ffffff",
                      border_color: str = "#000000",
                      margin_left: int = 0,
                      margin_right: int = 0,
                      ) -> None:
        '''
        Insert a chat bubble in `self.__conversation_console`.

        :param html_snippet:     The content of the bubble in HTML format.
        :param background_color: The background color of the bubble.
        :param border_color:     The color of the bubble border.
        :param margin_left:      Margin on the left side for the bubble.
        :param margin_right:     Margin on the right side for the bubble.
        '''
        if qt.sip.isdeleted(self.__conversation_console):
            return
        #& Prepare format for new frame
        frame_format = qt.QTextFrameFormat()
        frame_format.setBackground(qt.QColor(background_color))
        frame_format.setBorder(1)
        frame_format.setPadding(8)
        frame_format.setMargin(8)
        frame_format.setBorderStyle(
            qt.QTextFrameFormat.BorderStyle.BorderStyle_Solid
        )
        frame_format.setBorderBrush(qt.QBrush(qt.QColor(border_color)))
        if margin_left > 0:
            frame_format.setLeftMargin(margin_left)
        if margin_right > 0:
            frame_format.setRightMargin(margin_right)

        #& Create and insert the new frame
        if self.__animation_running:
            print("WARNING: insert_bubble() called while animation was running! Insert before it.")
            raise Exception()
            # Insert before the animation bubble
            animation_frame = self.__bubble_frames[-1]  # Animation bubble is always the last frame
            insert_pos = animation_frame.firstPosition()
            cursor = self.__conversation_console.textCursor()
            cursor.setPosition(insert_pos)
            frame = cursor.insertFrame(frame_format)
            # Insert the new frame before the animation frame in the list
            self.__bubble_frames.insert(-1, frame)
        else:
            # Insert at the end
            cursor = self.__conversation_console.textCursor()
            cursor.movePosition(qt.QTextCursor.MoveOperation.End)
            frame = cursor.insertFrame(frame_format)
            self.__bubble_frames.append(frame)

        #& Insert content in the new frame
        # Move cursor to start of the frame and insert HTML content
        cursor.setPosition(frame.firstPosition())
        cursor.insertHtml(html_snippet)
        # Move cursor outside the frame
        cursor.setPosition(frame.lastPosition() + 1)
        cursor.movePosition(qt.QTextCursor.MoveOperation.End)
        return
```

and the method that replaces the content from the last bubble:

```python
    def replace_last_bubble(self, html_snippet:str) -> None:
        '''
        Replace the content of the last text bubble (without deleting it!).
        '''
        if qt.sip.isdeleted(self.__conversation_console):
            return
        if not self.__bubble_frames:
            # No frames found. Insert a new one.
            self.insert_bubble(html_snippet)
            return
        # Get the last frame inserted
        frame = self.__bubble_frames[-1]
        if qt.sip.isdeleted(frame):
            print(f"ERROR: self.__bubble_frames[-1] pointed at empty shell!")
            self.__bubble_frames.pop()
            self.replace_last_bubble(html_snippet)
            return
        # Update the content of the frame
        cursor = self.__conversation_console.textCursor()
        cursor.setPosition(frame.firstPosition())
        cursor.setPosition(frame.lastPosition(), qt.QTextCursor.MoveMode.KeepAnchor)
        # Replace the content
        cursor.removeSelectedText()
        cursor.insertHtml(html_snippet)
        # Ensure the cursor is moved outside the frame after update
        cursor.setPosition(frame.lastPosition() + 1)
        cursor.movePosition(qt.QTextCursor.MoveOperation.End)
        return
```

And a method that deletes the last text bubble:
```python
    def remove_last_bubble(self) -> None:
        '''
        Remove the most recent chat bubble. Not only the content is removed, but the entire frame.
        '''
        if qt.sip.isdeleted(self.__conversation_console):
            return
        if not self.__bubble_frames:
            return  # No frames to remove
        # Get the last frame inserted
        frame = self.__bubble_frames.pop()
        if qt.sip.isdeleted(frame):
            print(f"ERROR: self.__bubble_frames[-1] points at empty shell!")
            self.remove_last_bubble()
            return
        # Select the frame's content
        cursor = self.__conversation_console.textCursor()
        cursor.setPosition(frame.firstPosition())
        cursor.setPosition(frame.lastPosition() + 1, qt.QTextCursor.MoveMode.KeepAnchor)
        # Remove the selected text (which includes the frame)
        cursor.removeSelectedText()
        # Optionally, move the cursor to the end
        cursor.movePosition(qt.QTextCursor.MoveOperation.End)
        return
```

So far, I have two kinds of text bubbles: "question bubbles" and "answer bubbles". I created an
insertion method for each:

```python
    def insert_question_bubble(self, html_question: str) -> None:
        '''
        Insert a question bubble in `self.__conversation_console`, aligned to the right.

        :param html_question: The question in HTML format.
        '''
        if qt.sip.isdeleted(self.__conversation_console):
            return
        pygments_css = self.__remove_background_color(
            pieces.helperfunctions.get_css_highligthing_code()
        )
        combined_text = f"""
<html>
<head>
    <style>
        {pygments_css}
    </style>
</head>
<body style='color: {data.theme["fonts"]["default"]["color"]};'>
    {html_question}
</body>
</html>
"""
        #$ Insert the question as a new bubble
        self.insert_bubble(
            html_snippet     = combined_text,
            background_color = data.theme["pieces_question_background"],
            border_color     = data.theme["pieces_question_border"],
            margin_left      = 100,
        )
        return

    def insert_answer_bubble(self, html_answer: str) -> None:
        '''
        Insert an answer bubble in `self.__conversation_console`, aligned to the left.

        :param html_answer: The answer in HTML format.
        '''
        if qt.sip.isdeleted(self.__conversation_console):
            return
        pygments_css = self.__remove_background_color(
            pieces.helperfunctions.get_css_highligthing_code()
        )
        combined_text = f"""
<html>
<head>
    <style>
        {pygments_css}
    </style>
</head>
<body>
    {html_answer}
</body>
</html>
"""

        #$ Insert the answer as a new bubble
        self.insert_bubble(
            html_snippet     = combined_text,
            background_color = data.theme["pieces_answer_background"],
            border_color     = data.theme["pieces_answer_border"],
            margin_right     = 100,
        )
        return
```

All of this works great for the simple use-case where the AI gives me a complete answer in one 
go. However, the reality is that the AI gives the answer as a generator-object. In other words, 
it gives me like a few hundred answer snippets (each being one or more tokens).

For that reason, I need to replace my function `insert_answer_bubble(html_snippet)` with the
following set of functions:

1) `start_answer_bubble()`
Create a new answer bubble with the CSS tags prepared. The `<body></body>` is empty though.

2) `add_answer_snippet(html_snippet)`
Add a snippet of html into the body of the answer bubble.

3) `finish_answer_bubble()`
Finish the answer bubble. Move the cursor to the end, so it is ready to start a new bubble upon 
   request.