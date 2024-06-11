import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import altair as alt
import time

# Set page configuration to wide mode
st.set_page_config(layout="wide")

# Function to simulate real-time data
def generate_real_time_data():
    mttr_hours = np.random.randint(2, 6)
    mttr_percentage_change = np.random.uniform(-5, 5)
    mtbf_hours = np.random.randint(24, 150)
    mtbf_percentage_change = np.random.uniform(-5, 5)
    quality = np.random.uniform(80, 95)
    performance = np.random.uniform(80, 95)
    availability = mtbf_hours / (mtbf_hours + mttr_hours)*100
    oee = (quality * performance * availability) / 10000

    return {
        "mttr": {"Hours": mttr_hours, "Percentage Change": mttr_percentage_change},
        "mtbf": {"Hours": mtbf_hours, "Percentage Change": mtbf_percentage_change},
        "oee": {"OEE": oee, "Quality": quality, "Performance": performance, "Availability": availability},
    }

if 'kpi_data' not in st.session_state:
    st.session_state.kpi_data = {
        'mttr': [],
        'mtbf': [],
        'oee': [],
        'month': []
    }

if 'maintenance_data' not in st.session_state:
    st.session_state.maintenance_data = pd.DataFrame({
        'Task': ['Check Sensors', 'Lubricate Bearings', 'Inspect Hydraulic System', 'Align Components', 'Check Interlocks'],
        'ScheduledDate': ['2023-12-01', '2023-12-07', '2023-12-15', '2023-12-20', '2023-12-25'],
        'CompletionDate': ['2023-12-01', '2023-12-07', '2023-12-16', '2023-12-21', ''],
        'Status': ['Completed', 'Completed', 'Completed', 'Completed', 'Pending']
    })
    st.session_state.maintenance_data['ScheduledDate'] = pd.to_datetime(st.session_state.maintenance_data['ScheduledDate'])
    st.session_state.maintenance_data['CompletionDate'] = pd.to_datetime(st.session_state.maintenance_data['CompletionDate'], errors='coerce')

def update_task(index, status, scheduled_date, completion_date):
    st.session_state.maintenance_data.at[index, 'Status'] = status
    st.session_state.maintenance_data.at[index, 'ScheduledDate'] = scheduled_date
    st.session_state.maintenance_data.at[index, 'CompletionDate'] = completion_date

def page_1():
    data = st.session_state.maintenance_data

    # Section to add a new task
    st.header("Add a New Task")
    with st.form("add_task"):
        new_task = st.text_input("Task Name")
        new_scheduled_date = st.date_input("Scheduled Date")
        new_completion_date = st.date_input("Completion Date", key='new_completion_date', value=None)
        new_status = st.selectbox("Status", ['Pending', 'Completed', 'Planned'], key='new_status')
        submit_button = st.form_submit_button("Add Task")
        
        if submit_button:
            new_data = pd.DataFrame({
                'Task': [new_task],
                'ScheduledDate': [new_scheduled_date],
                'CompletionDate': [new_completion_date if new_completion_date else None],
                'Status': [new_status]
            })
            st.session_state.maintenance_data = pd.concat([data, new_data], ignore_index=True)
            st.session_state.maintenance_data['ScheduledDate'] = pd.to_datetime(st.session_state.maintenance_data['ScheduledDate'])
            st.session_state.maintenance_data['CompletionDate'] = pd.to_datetime(st.session_state.maintenance_data['CompletionDate'], errors='coerce')
            st.success("Task added successfully!")

    # Section to display and update existing tasks
    st.header("Maintenance Tasks")
    for i in range(len(data)):
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        col1.write(data['Task'][i])
        new_scheduled_date = col2.date_input(f'Scheduled Date for {data["Task"][i]}', value=data['ScheduledDate'][i], key=f'scheduled_date_{i}')
        new_completion_date = col3.date_input(f'Completion Date for {data["Task"][i]}', value=data['CompletionDate'][i] if pd.notnull(data['CompletionDate'][i]) else None, key=f'completion_date_{i}')
        new_status = col4.selectbox(f'Status for {data["Task"][i]}', ['Pending', 'Completed', 'Planned'], index=['Pending', 'Completed', 'Planned'].index(data['Status'][i]), key=f'status_{i}')
        col5.write(data['Status'][i])
        if col6.button('Delete', key=f'delete_{i}'):
            st.session_state.maintenance_data = data.drop(i).reset_index(drop=True)
            break
        update_task(i, new_status, new_scheduled_date, new_completion_date)

def page_2():
    # Header
    st.title("Preventive Maintenance Plan Dashboard")

    # Update real-time data
    data = generate_real_time_data()
    if 'month_counter' not in st.session_state:
        st.session_state.month_counter = 1

    st.session_state.kpi_data['mttr'].append(data["mttr"]["Hours"])
    st.session_state.kpi_data['mtbf'].append(data["mtbf"]["Hours"])
    st.session_state.kpi_data['oee'].append(data["oee"]["OEE"])
    st.session_state.kpi_data['month'].append(st.session_state.month_counter)

    # Increment month counter and reset to 1 if it exceeds 12
    st.session_state.month_counter += 1
    if st.session_state.month_counter > 12:
        st.session_state.month_counter = 1

    # Ensure that only the latest 12 data points are kept
    if len(st.session_state.kpi_data['mttr']) > 12:
        st.session_state.kpi_data['mttr'] = st.session_state.kpi_data['mttr'][-12:]
        st.session_state.kpi_data['mtbf'] = st.session_state.kpi_data['mtbf'][-12:]
        st.session_state.kpi_data['oee'] = st.session_state.kpi_data['oee'][-12:]
        st.session_state.kpi_data['month'] = st.session_state.kpi_data['month'][-12:]

    # MTTR and MTBF Visualization
    st.header("Maintenance KPIs")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Mean Time Between Failures (MTBF)")
        delta_color = "inverse" if len(st.session_state.kpi_data['mtbf']) > 1 and st.session_state.kpi_data['mtbf'][-1] < st.session_state.kpi_data['mtbf'][-2] else "normal"
        st.metric("MTBF Hours", st.session_state.kpi_data['mtbf'][-1], f"{((st.session_state.kpi_data['mtbf'][-1] - st.session_state.kpi_data['mtbf'][-2]) / st.session_state.kpi_data['mtbf'][-2]) * 100:.2f}%" if len(st.session_state.kpi_data['mtbf']) > 1 else "", delta_color=delta_color)
        st.line_chart(pd.DataFrame({'Month': st.session_state.kpi_data['month'], 'MTBF': st.session_state.kpi_data['mtbf']}).set_index('Month'))
    with col2:
        st.subheader("Mean Time to Repair (MTTR)")
        delta_color = "inverse" if len(st.session_state.kpi_data['mttr']) > 1 and st.session_state.kpi_data['mttr'][-1] < st.session_state.kpi_data['mttr'][-2] else "normal"
        st.metric("MTTR Hours", st.session_state.kpi_data['mttr'][-1], f"{((st.session_state.kpi_data['mttr'][-1] - st.session_state.kpi_data['mttr'][-2]) / st.session_state.kpi_data['mttr'][-2]) * 100:.2f}%" if len(st.session_state.kpi_data['mttr']) > 1 else "", delta_color='inverse')
        st.line_chart(pd.DataFrame({'Month': st.session_state.kpi_data['month'], 'MTTR': st.session_state.kpi_data['mttr']}).set_index('Month'))

    col1, col2 = st.columns(2)
    with col1:
        # OEE Visualization
        st.header("Overall Equipment Effectiveness (OEE)")

        oee_value = st.session_state.kpi_data['oee'][-1]
        st.metric("OEE", f"{oee_value:.2f}%")

        # Horizontal bar chart for OEE components using Altair
        oee_components = pd.DataFrame({
            'Component': ['Quality', 'Performance', 'Availability'],
            'Value': [data["oee"]["Quality"], data["oee"]["Performance"], data["oee"]["Availability"]]
        })

        chart = alt.Chart(oee_components).mark_bar().encode(
            x=alt.X('Value:Q'),
            y=alt.Y('Component:N', sort='-x'),
            color=alt.Color('Component:N', scale=alt.Scale(range=['#5a61bd', '#7178df', '#9ca2ef'])),
            tooltip=['Component', 'Value']
        ).properties(
            width=600,
            height=300,
            title='OEE Components'
        ).configure_axis(
            labelColor='black',
            titleColor='black'
        ).configure_view(
            strokeWidth=0,
            fillOpacity=0
        ).configure_title(
            color='black'
        ).configure_legend(
            titleColor='black',
            labelColor='black'
        )

        st.altair_chart(chart, use_container_width=True)
    with col2:
        # Calculate completion rate
        filtered_data = st.session_state.maintenance_data[st.session_state.maintenance_data['Status'] != 'Planned']
        filtered_data['StatusValue'] = filtered_data['Status'].apply(lambda x: 1 if x == 'Completed' else 0)
        completion_rate = filtered_data['StatusValue'].mean() * 100 if len(filtered_data) > 0 else 0

        st.subheader("Completion Rate")
        st.metric("Completion Rate", f"{completion_rate:.2f}%")

        # Donut chart for completion rate with specified colors
        completion_status_counts = filtered_data['Status'].value_counts()
        fig_pie = px.pie(
            values=completion_status_counts.values, 
            names=completion_status_counts.index,
            hole=0.6,
            color_discrete_sequence=['#5a61bd', '#7178df']
        )
        st.plotly_chart(fig_pie)

# Page navigation
page = st.sidebar.selectbox("Select a page", ["Maintenance Tasks", "Dashboard"])

if page == "Maintenance Tasks":
    page_1()
else:
    page_2()

    # Simulate real-time data update
    time.sleep(3)
    st.experimental_rerun()
