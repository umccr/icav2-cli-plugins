#!/usr/bin/env python

"""
Helpers to plot the gantt chart

Inspiration from this gantt tutorial and relevant code
https://towardsdatascience.com/gantt-charts-with-pythons-matplotlib-395b7af72d72
https://gist.github.com/Thiagobc23/fc12c3c69fbb90ac64b594f2c3641fcf
"""

import re
from pathlib import Path
from typing import List
import pytz

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter, date2num
from matplotlib.patches import Patch
from datetime import datetime

from libica.openapi.v2.model.analysis_step import AnalysisStep

from utils.projectanalysis_helpers import get_analysis

STATUS_TO_COLOUR_MAP = {
    "FAILED": "#E71414",  # Bright Red
    "DONE": "#77E714", # Pastel Green
    "RUNNING": "#E7D714",  # Pastel Yellow
    "INTERRUPTED": "#8714E7",  # Purple
    "ABORTED": "#8714E7",  # Purple
    "WAITING": "#C1C1C1"  # Grey
}


def time_delta_to_human_readable(total_seconds: int) -> str:
    """
    
    Args:
        total_seconds: a

    Returns:

    """
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    # Formatted only for hours and minutes as requested
    return '%02d:%02d' % (hours, minutes)


def analysis_list_to_df(workflow_steps: List[AnalysisStep]) -> pd.DataFrame:
    # Map the list of workflow steps to a dataframe
    """
    Given a list of workflows, map and convert to a dataframe
    Args:
        workflow_steps: List of Analysis Steps

    Returns: A DataFrame with the following columns
            * task_id
            * task_name
            * task_status
            * task_is_technical
            * task_queue_date
            * task_start_date
            * task_end_date
    """
    return pd.DataFrame(
        list(
            map(
                lambda x:
                {
                    "task_id": x.id,
                    "task_name": x.name,
                    "task_status": x.status,
                    "task_is_technical": x.technical,
                    "task_queue_date": x.queue_date,
                    "task_start_date": x.start_date,
                    "task_end_date": x.end_date
                },
                workflow_steps
            )
        )
    )


def filter_workflow_steps_df(workflow_steps_df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter out the workflow steps dataframe

    This completes the following:
    1. Drops all of the intermediate technical step
       All of the technical intermediate steps have an overarching step that covers their start and end anyway
    2. Renames Technical Steps


    Args:
        workflow_steps_df:
          Contains the following columns
            * task_id
            * task_name
            * task_status
            * task_is_technical
            * task_queue_date
            * task_start_date
            * task_end_date
    Returns:
        DataFrame with the following columns
            * task_id
            * task_name
            * task_status
            * task_is_technical
            * task_queue_date
            * task_start_date
            * task_end_date

    """
    # Check if a technical intermediate step that needs to be dropped
    workflow_steps_df["drop_step"] = workflow_steps_df.copy().apply(
        lambda x:
        ( re.match(r"(setup_environment|prepare_input_data|finalize_output_data|pipeline_runner)\.\d+", x["task_name"]) is not None
           or x["task_name"].startswith("Workflow_pre-run")
        ) and x["task_is_technical"],
        axis="columns"
    )

    # Drop steps that need to be dropped and remove the drop_step column
    workflow_steps_df = workflow_steps_df.query("drop_step==False")
    workflow_steps_df = workflow_steps_df.drop(columns="drop_step")

    # Rename workflow_monitor-0 to Workflow Monitor
    workflow_steps_df["task_name"] = workflow_steps_df["task_name"].apply(
        lambda x: re.sub("^Workflow_monitor\-\d+$", "Workflow Monitor", x)
    )

    # Rename technical Steps to Tch. <name>
    workflow_steps_df["task_name"] = workflow_steps_df.apply(
        lambda x: f"Tch: {x['task_name']}" if x['task_is_technical'] else x['task_name'],
        axis="columns"
    )

    # FIXME handle null end dates and start dates

    return workflow_steps_df


def add_task_duration_columns(workflow_steps_df: pd.DataFrame) -> pd.DataFrame:
    """
    Add the duration columns for plotting.
    Plotting uses horizontal bars that need 'height/length' values.
    These values are represented by the task duration.
    Since we also want to know task 'pending' time we add in a 'task_pending_duration' column
    represented by task_start_date - task_queue_date

    Args:
        workflow_steps_df:
          Contains the following columns
            * task_id
            * task_name
            * task_status
            * task_is_technical
            * task_queue_date
            * task_start_date
            * task_end_date
    Returns:
        DataFrame with the following columns
            * task_id
            * task_name
            * task_status
            * task_is_technical
            * task_queue_date
            * task_start_date
            * task_end_date
            * task_pending_td
            * task_duration_td
    """

    # Best practise to copy an input object, rather than edit inplace
    workflow_steps_df = workflow_steps_df.copy()

    workflow_steps_df["task_pending_td"] = workflow_steps_df.apply(
        lambda x: x.task_start_date - x.task_queue_date,
        axis="columns"
    )

    workflow_steps_df["task_duration_td"] = workflow_steps_df.apply(
        lambda x: x.task_end_date - x.task_start_date,
        axis="columns"
    )

    return workflow_steps_df


def add_task_colour_column(workflow_steps_df: pd.DataFrame) -> pd.DataFrame:
    """

    Args:
        workflow_steps_df:
          Contains the following columns
            * task_id
            * task_name
            * task_status
            * task_is_technical
            * task_queue_date
            * task_start_date
            * task_end_date
            * task_pending_td
            * task_duration_td
    Returns:
        DataFrame with the following columns
            * task_id
            * task_name
            * task_status
            * task_is_technical
            * task_queue_date
            * task_start_date
            * task_end_date
            * task_pending_td
            * task_duration_td
            * task_colour
    """

    # Task colour depends on the task status
    workflow_steps_df = workflow_steps_df.copy()

    workflow_steps_df["task_colour"] = workflow_steps_df.apply(
        lambda x: STATUS_TO_COLOUR_MAP[x["task_status"]],
        axis="columns"
    )

    return workflow_steps_df


def plot_workflow_steps_df(workflow_steps_df: pd.DataFrame, output_path: Path, project_id: str, analysis_id: str):
    """

    Args:
        workflow_steps_df: A dataframe with the following columns
          Contains the following columns
            * task_id
            * task_name
            * task_status
            * task_is_technical
            * task_queue_date
            * task_start_date
            * task_end_date
            * task_pending_td
            * task_duration_td
        output_path: Path to the output png file
        analysis_id: The workflow ID
    Returns:
        None
    """

    # Sort steps by task start date
    workflow_steps_df = workflow_steps_df.copy().\
        sort_values(by="task_queue_date", ascending=False).reset_index()

    # Use timeCreated as the start of the analysis
    analysis_creation_time = get_analysis(project_id, analysis_id).time_created
    # Add in queue date td and start date td for date time
    # task queue date is the first one to start up
    workflow_steps_df["task_queue_td"] = workflow_steps_df["task_queue_date"] - analysis_creation_time
    workflow_steps_df["task_start_td"] = workflow_steps_df["task_start_date"] - analysis_creation_time
    workflow_steps_df["task_end_td"] = workflow_steps_df["task_end_date"] - analysis_creation_time

    # Convert time deltas to numbers
    zero_date = datetime.fromtimestamp(0, tz=pytz.utc)
    workflow_steps_df["task_queue_tdn"] = workflow_steps_df["task_queue_td"].apply(lambda x: date2num(zero_date + x))
    workflow_steps_df["task_start_tdn"] = workflow_steps_df["task_start_td"].apply(lambda x: date2num(zero_date + x))
    workflow_steps_df["task_end_tdn"] = workflow_steps_df["task_end_td"].apply(lambda x: date2num(zero_date + x))
    workflow_steps_df["task_end_tdn"] = workflow_steps_df["task_end_td"].apply(lambda x: date2num(zero_date + x))
    workflow_steps_df["task_pending_tdn"] = workflow_steps_df["task_pending_td"].apply(lambda x: date2num(zero_date + x))
    workflow_steps_df["task_duration_tdn"] = workflow_steps_df["task_duration_td"].apply(lambda x: date2num(zero_date + x))

    # Part 1 - use fig to create a plot with two axes
    # The second axes is merely a place holder so we have room for the legend at the bottom
    # FIXME, use facecolor to enter darkmode if desired
    fig: plt.Figure
    ax: plt.Axes
    ax1: plt.Axes
    fig, (ax, ax1) = plt.subplots(2, figsize=(16, 6), gridspec_kw={'height_ratios': [6, 1]})

    # Add bars to include
    # Add in pending bars (hashed
    ax.barh(
        workflow_steps_df["task_name"],
        workflow_steps_df["task_pending_tdn"],
        left=workflow_steps_df["task_queue_tdn"],
        color="grey",
        hatch="/",
        alpha=0.5
    )

    # Add in task duration bars
    ax.barh(
        workflow_steps_df["task_name"],
        workflow_steps_df["task_duration_tdn"],
        left=workflow_steps_df["task_start_tdn"],
        color=workflow_steps_df["task_colour"]
    )

    # Create labels on left hand side of bar graph
    for idx, row in workflow_steps_df.iterrows():
        ax.text(
            x=row["task_queue_tdn"],
            y=idx,
            s=row["task_name"] + "  ",
            va='center',
            ha='right',
            alpha=0.8,
            color='k'
        )

    # Create time labels on the right hand side of bar graph
    for idx, row in workflow_steps_df.iterrows():
        ax.text(
            x=row["task_end_tdn"],
            y=idx,
            s=" " +
                 time_delta_to_human_readable(row["task_pending_td"].total_seconds()) +
                 " / " +
                 time_delta_to_human_readable(row["task_duration_td"].total_seconds()),
            va='center',
            ha='left',
            alpha=0.8,
            color='k'
        )

    # Set grid lines
    ax.set_axisbelow(True)
    ax.xaxis.grid(
        color='k',
        linestyle='dashed',
        alpha=0.4,
        which='both'
    )

    # Set xticks
    # Set formatter for xaxis
    ax.xaxis_date()
    ax.xaxis.set_major_formatter(DateFormatter("%H:%M"))

    # Align x-axis
    ax.set_xlim(date2num(zero_date), workflow_steps_df["task_end_tdn"].max())

    # Set titles
    fig.suptitle(f"Gantt Chart of analysis '{analysis_id}'")
    ax.set_ylabel("")
    ax.set_xlabel("Duration (HH:MM)")

    # Set legend elements
    legend_elements = list(
        map(
            lambda kv: Patch(
                facecolor=kv[1],
                label=kv[0],
                hatch="/" if kv[1] == "WAITING" else None
            ),
            STATUS_TO_COLOUR_MAP.items()
        )
    )

    legend = ax1.legend(handles=legend_elements, loc='center', ncol=len(STATUS_TO_COLOUR_MAP), frameon=False)
    plt.setp(legend.get_texts(), color='k')

    # Remove yticks
    ax.set_yticks([])

    # Remove ax1
    ax1.spines['right'].set_visible(False)
    ax1.spines['left'].set_visible(False)
    ax1.spines['top'].set_visible(False)
    ax1.spines['bottom'].set_visible(False)
    ax1.set_xticks([])
    ax1.set_yticks([])

    # Plot figure
    plt.savefig(output_path)
