import traitlets
import ipyvuetify as v

# this was made to fix the date sort the date column needs a sortable value
# so to keep MM/DD/YYYY format, you need the Date column to have 
# the timestamp, but display the formmated value. ipyvuetify 
# does not support {{ }} syntax in slots (see ipyvuetify issue 131)
# so use a thin wrapper of the v-data-table all props, except v-model
# get passed straight to teh template (so use camel- instead of snake- case)
# Seems more trouble than it's worth, when we can just use YYYY-MM-DD format
# Usage:
#  table = SortedDateTable(
#     items=data.value,
#     v_model=selected_rows.value,
#     on_v_model=selected_rows.set,
#     rvDataTableProps = dict(
#     singleSelect=False,
#     showSelect=True,
#     headers=[
#         {
#             "text": "Name",
#             "align": "start",
#             "sortable": True,
#             "value": "name",
#         },
#         {"text": "Date", "value": "date_ts"},
#         {"text": "Story", "value": "story"},
#         {"text": "Code", "value": "code"},
#         {"text": "ID", "value": "id", "align": "d-none"},
#         # {"text": "Expected size", "value": "expected_size"},
#         {"text": "Class Active", "value": "active"},
#         # {"text": "Asynchronous", "value": "asynchronous"},
#     ],
#     hideDefaultFooter=True,
#     ),
# )
# solara.display(table)


# sort with new items on top by default instead of by name
SORTED_DATA_TABLE_TEMPLATE = """
<template>
    <v-data-table
        :items="items"
        :sort-by="['date_ts']"
        :sort-desc="['true']"
        v-model="v_model"
        v-bind="rvDataTableProps"
    >
        <template v-slot:item.date_ts="{ item }">
            <td>{{ item.date }}</td>
        </template>
    </v-data-table>
</template>
"""

class SortedDateTable(v.VuetifyTemplate):
    items   = traitlets.List([]).tag(sync=True)
    v_model = traitlets.List([]).tag(sync=True)
    rvDataTableProps   = traitlets.Dict({}).tag(sync=True)

    @traitlets.default('template')
    def _template(self):
        return SORTED_DATA_TABLE_TEMPLATE