import tkinter
import tkinter.messagebox
import traceback
import urllib.parse
import webbrowser
from operator import methodcaller
from threading import Thread
from tkinter.scrolledtext import ScrolledText

from profeyelar.preferences import ProfilingPreferences


class InvalidTextInputError(Exception):
    def __init__(self, given_value: str):
        super().__init__(
            "[ERROR] The following value is not a valid value"
            f" for the corresponding input field: {given_value}"
        )


class MainFrame(tkinter.Frame):
    HEADING_FONT = ("Helvetica", 14)
    PADDING_SIZE = 10
    PROGRAM_NAME = "Prof. Eyelar"
    STANDARD_FONT = ("Helvetica", 10)
    SPINBOX_WIDTH = 40

    def __init__(self, root: tkinter.Tk, options):
        super().__init__(
            root, padx=self.PADDING_SIZE, pady=self.PADDING_SIZE / 2
        )
        self._root = root
        root.title(self.PROGRAM_NAME)
        self.row_count = 0
        self.parsed_settings = options
        self._add_widgets()

    def get_selected_preferences(self) -> ProfilingPreferences:
        ram_limit = int(self._ram_limit.get())
        return ProfilingPreferences(
            relative_urls=self._tell_provided_relative_urls(),
            repetitions=int(self._repetitions.get()),
            tracemalloc_enabled=self._tracemalloc_selected.get(),
            cprofile_enabled=self._cprofile_selected.get(),
            ram_limit=ram_limit or None,
            request_headers=self._build_request_headers(),
        )

    def freeze(self):
        self._start_button.config(state=tkinter.DISABLED)

    def unfreeze(self):
        self._start_button.config(state=tkinter.NORMAL)

    def notify_err(self, msg: str):
        tkinter.messagebox.showerror(
            self.PROGRAM_NAME, f"Invalid input: {msg}"
        )

    def _build_request_headers(self) -> dict[str, str]:
        headers_text = self._get_long_text_content(self._request_headers)
        lines = self._get_stripped_text_lines(headers_text)
        if len(lines) != headers_text.count(":"):
            raise InvalidTextInputError(headers_text)
        return {
            key: value.lstrip()
            for key, value in map(methodcaller("split", ":"), lines)
        }

    def _tell_provided_relative_urls(self) -> list[str]:
        full_text = self._get_long_text_content(self._requests)
        result = self._get_stripped_text_lines(full_text)
        if not result:
            raise ValueError("providing no URLs does not quite make sense.")
        return result

    def _get_long_text_content(self, widget: ScrolledText) -> str:
        return widget.get(1.0, tkinter.END)

    def _get_stripped_text_lines(self, text: str) -> str:
        stripped = (line.strip() for line in text.splitlines())
        return [line for line in stripped if line]

    def _set_encoded_value(self):
        current = self._unencoded.get()
        encoded = urllib.parse.quote_plus(current)
        self._encoded.set(encoded)

    def _add_widgets(self):
        self.grid()
        self._set_up_request_url_section()
        self._set_up_fields_filter_utility_section()
        self._set_up_request_options_section()
        self._set_up_profiling_options_section()
        self._set_up_buttons()
        self._set_up_status_bar()
        self.set_status_text("Ready")

    def _start_profiling_with_selected_preferences(self):
        try:
            prefs = self.get_selected_preferences()
            from profeyelar.launcher import start_profiling

            th = Thread(
                target=start_profiling,
                args=(self.parsed_settings, prefs, self),
            )
            th.start()
        except ValueError as e:
            tkinter.messagebox.showerror(
                self.PROGRAM_NAME, f"Invalid input: {e}"
            )
        except Exception as e:
            traceback.print_exception(e)
            tkinter.messagebox.showerror(
                self.PROGRAM_NAME, f"{e.__class__.__name__}: {e}"
            )

    def _set_up_buttons(self):
        self.frame_buttons = tkinter.Frame(self)
        self.frame_buttons.grid(
            column=0,
            row=self.row_count,
            padx=self.PADDING_SIZE,
            pady=self.PADDING_SIZE / 2,
            sticky="ew",
        )
        self.frame_buttons.columnconfigure(0, weight=2)
        self.frame_buttons.columnconfigure(1, weight=1)
        self.frame_buttons.columnconfigure(2, weight=1)

        self._start_button = tkinter.Button(
            self.frame_buttons,
            text="Start container & run requests",
            command=self._start_profiling_with_selected_preferences,
        )
        self._start_button.grid(
            column=0,
            row=0,
            sticky="w",
            padx=self.PADDING_SIZE,
            pady=self.PADDING_SIZE / 2,
        )

        docs_url = self.parsed_settings["service__api_docs_url"]
        if docs_url:
            tkinter.Button(
                self.frame_buttons,
                text="Open API docs",
                command=lambda: webbrowser.open_new_tab(docs_url),
            ).grid(
                column=1,
                row=0,
                padx=self.PADDING_SIZE,
                pady=self.PADDING_SIZE / 2,
                sticky="w",
            )

        tkinter.Button(
            self.frame_buttons, text="Quit", command=self._root.destroy
        ).grid(
            column=2,
            row=0,
            padx=self.PADDING_SIZE,
            pady=self.PADDING_SIZE / 2,
            sticky="e",
        )

        self._increment_row_count()

    def _set_up_profiling_options_section(self):
        self.frame_profiling_options = tkinter.Frame(self)
        self.frame_profiling_options.grid(
            column=0,
            row=self.row_count,
            padx=self.PADDING_SIZE,
            pady=self.PADDING_SIZE / 2,
            sticky="ew",
        )
        self.frame_profiling_options.columnconfigure(0, weight=1)
        self.frame_profiling_options.columnconfigure(1, weight=2)

        tkinter.Label(
            self.frame_profiling_options,
            text="Profiling options",
            justify="left",
            font=self.HEADING_FONT,
        ).grid(
            column=0,
            row=0,
            padx=self.PADDING_SIZE,
            pady=self.PADDING_SIZE / 2,
            sticky="w",
        )

        tkinter.Label(
            self.frame_profiling_options,
            text="Enable tracemalloc",
            font=self.STANDARD_FONT,
            justify="left",
        ).grid(
            column=0,
            row=1,
            padx=self.PADDING_SIZE,
            pady=self.PADDING_SIZE / 2,
            sticky="w",
        )
        self._tracemalloc_selected = tkinter.BooleanVar()
        tkinter.Checkbutton(
            self.frame_profiling_options, variable=self._tracemalloc_selected
        ).grid(
            column=1,
            row=1,
            padx=self.PADDING_SIZE,
            pady=self.PADDING_SIZE / 2,
            sticky="e",
        )

        tkinter.Label(
            self.frame_profiling_options,
            text="Enable cProfile",
            font=self.STANDARD_FONT,
            justify="left",
        ).grid(
            column=0,
            row=2,
            padx=self.PADDING_SIZE,
            pady=self.PADDING_SIZE / 2,
            sticky="w",
        )
        self._cprofile_selected = tkinter.BooleanVar()
        tkinter.Checkbutton(
            self.frame_profiling_options, variable=self._cprofile_selected
        ).grid(
            column=1,
            row=2,
            padx=self.PADDING_SIZE,
            pady=self.PADDING_SIZE / 2,
            sticky="e",
        )

        tkinter.Label(
            self.frame_profiling_options,
            text="Limit RAM to given amount of MiB\n(0 = unlimited)",
            font=self.STANDARD_FONT,
            justify="left",
        ).grid(
            column=0,
            row=3,
            padx=self.PADDING_SIZE,
            pady=self.PADDING_SIZE / 2,
            sticky="nw",
        )
        self._ram_limit = tkinter.Spinbox(
            self.frame_profiling_options,
            from_=0,
            increment=16,
            to=2048,
            width=self.SPINBOX_WIDTH,
        )
        self._ram_limit.grid(
            column=1,
            row=3,
            padx=self.PADDING_SIZE,
            pady=self.PADDING_SIZE / 2,
            sticky="sne",
        )
        self._increment_row_count()

    def _set_up_request_options_section(self):
        self.frame_request_options = tkinter.Frame(self)
        self.frame_request_options.grid(
            column=0,
            row=self.row_count,
            padx=self.PADDING_SIZE,
            pady=self.PADDING_SIZE / 2,
            sticky="ew",
        )
        self.frame_request_options.columnconfigure(0, weight=1)
        self.frame_request_options.columnconfigure(1, weight=2)

        label_options = tkinter.Label(
            self.frame_request_options,
            text="Request options",
            font=self.HEADING_FONT,
        )
        label_options.grid(
            column=0,
            row=0,
            padx=self.PADDING_SIZE,
            pady=self.PADDING_SIZE / 2,
            sticky="w",
        )
        tkinter.Label(
            self.frame_request_options,
            text="Repetitions",
            font=self.STANDARD_FONT,
        ).grid(
            column=0,
            row=1,
            padx=self.PADDING_SIZE,
            pady=self.PADDING_SIZE / 2,
            sticky="w",
        )
        self._repetitions = tkinter.Spinbox(
            self.frame_request_options,
            from_=1,
            increment=1,
            to=1000,
            width=self.SPINBOX_WIDTH,
        )
        self._repetitions.grid(
            column=1,
            row=1,
            padx=self.PADDING_SIZE,
            pady=self.PADDING_SIZE / 2,
            sticky="e",
        )

        tkinter.Label(
            self.frame_request_options, text="Headers", font=self.STANDARD_FONT
        ).grid(
            column=0,
            row=2,
            padx=self.PADDING_SIZE,
            pady=self.PADDING_SIZE / 2,
            sticky="nw",
        )
        self._request_headers = ScrolledText(
            self.frame_request_options, height=3, width=46
        )
        self._request_headers.grid(
            column=1,
            row=2,
            sticky="e",
            padx=self.PADDING_SIZE,
            pady=self.PADDING_SIZE / 2,
        )
        self._increment_row_count()

    def _set_up_fields_filter_utility_section(self):
        self.frame_utilities = tkinter.Frame(self)
        self.frame_utilities.grid(
            column=0,
            row=self.row_count,
            padx=self.PADDING_SIZE,
            pady=self.PADDING_SIZE / 2,
            sticky="ew",
        )
        self.frame_utilities.columnconfigure(0, weight=2)
        self.frame_utilities.columnconfigure(1, weight=1)
        self.frame_utilities.columnconfigure(2, weight=2)

        tkinter.Label(
            self.frame_utilities,
            text="Helper: Encode URL Parameters",
            font=self.HEADING_FONT,
        ).grid(
            column=0,
            columnspan=3,
            row=0,
            padx=self.PADDING_SIZE,
            pady=self.PADDING_SIZE / 2,
        )
        self._unencoded = tkinter.StringVar()
        tkinter.Entry(
            self.frame_utilities, textvariable=self._unencoded, width=25
        ).grid(
            column=0,
            row=1,
            padx=self.PADDING_SIZE,
            pady=self.PADDING_SIZE / 2,
        )
        tkinter.Button(
            self.frame_utilities,
            text="→ Encode",
            command=self._set_encoded_value,
        ).grid(
            column=1,
            row=1,
            padx=self.PADDING_SIZE,
            pady=self.PADDING_SIZE / 2,
        )
        self._encoded = tkinter.StringVar()
        tkinter.Entry(
            self.frame_utilities, textvariable=self._encoded, width=25
        ).grid(
            column=2,
            row=1,
            padx=self.PADDING_SIZE,
            pady=self.PADDING_SIZE / 2,
        )
        self._increment_row_count()

    def _set_up_request_url_section(self):
        self.frame_request_urls = tkinter.Frame(self)
        self.frame_request_urls.grid(
            column=0,
            row=self.row_count,
            padx=self.PADDING_SIZE,
            pady=self.PADDING_SIZE / 2,
            sticky="ew",
        )

        tkinter.Label(
            self.frame_request_urls,
            text="Request URLs",
            font=self.HEADING_FONT,
        ).grid(
            column=0,
            row=0,
            padx=self.PADDING_SIZE,
            pady=self.PADDING_SIZE / 2,
            sticky="w",
        )
        tkinter.Label(
            self.frame_request_urls,
            text=(
                "Please enter relative request URLs here, "
                "e. g. /stores/?fields=%5Bid%2Cname%5D"
            ),
            font=self.STANDARD_FONT,
        ).grid(
            column=0,
            row=1,
            padx=self.PADDING_SIZE,
            pady=self.PADDING_SIZE / 2,
            sticky="w",
        )
        self._requests = ScrolledText(self.frame_request_urls)
        self._requests.grid(
            column=0,
            row=2,
            padx=self.PADDING_SIZE,
            pady=self.PADDING_SIZE / 2,
        )
        self._increment_row_count()

    def _set_up_status_bar(self):
        self.frame_status_bar = tkinter.Frame(self)
        self.frame_status_bar.grid(
            column=0,
            row=self.row_count,
            padx=self.PADDING_SIZE,
            pady=self.PADDING_SIZE / 2,
            sticky="ew",
        )

        self._status_bar = tkinter.Label(
            self.frame_status_bar, text="", font=self.STANDARD_FONT
        )
        self._status_bar.grid(
            column=0,
            row=0,
            sticky="w",
            padx=self.PADDING_SIZE,
            pady=self.PADDING_SIZE / 2,
        )

        self._increment_row_count()

    def set_status_text(self, status: str):
        self._status_bar.config(text=f"STATUS: {status}")

    def enter_main_loop(self):
        self._root.mainloop()

    def _increment_row_count(self):
        self.row_count += 1
