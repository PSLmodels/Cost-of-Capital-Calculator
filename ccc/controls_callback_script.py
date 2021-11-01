CONTROLS_CALLBACK_SCRIPT = """
var equip_data = equip_source.data;
var struc_data = struc_source.data;

var c_pt_button = c_pt_buttons.active;
var format_button = format_buttons.active;
var type_button = type_buttons.active;
var interest_button = interest_buttons.active;

var n_pt_str, format_str, type_str, interest_button
var c_pt_title, interest_title

if (c_pt_button == 0) {
    c_pt_str = '_c';
    c_pt_title = 'Corporate';
} else if (c_pt_button == 1) {
    c_pt_str = '_pt';
    c_pt_title = 'Noncorporate';
}

if (format_button == 0) {
    format_str = 'base_';
} else if (format_button == 1) {
    format_str = 'reform_';
} else if (format_button == 2) {
    format_str = 'change_';
}

if (type_button == 0) {
    type_str = '_mix'
} else if (type_button == 1) {
    type_str = '_e'
} else if (type_button == 2) {
    type_str = '_d'
}

if (interest_button == 0) {
    interest_str = '_mettr';
    equip_plot.attributes.renderers[0].axis_label =
        'Marginal effective total tax rate'
    struc_plot.attributes.renderers[0].axis_label =
        'Marginal effective total tax rate'
    interest_title = 'Marginal Effective Total Tax Rates'
} else if (interest_button == 1) {
    interest_str = '_metr';
    equip_plot.attributes.renderers[0].axis_label =
        'Marginal effective tax rate'
    struc_plot.attributes.renderers[0].axis_label =
        'Marginal effective tax rate'
    interest_title = 'Marginal Effective Tax Rates'
} else if (interest_button == 2) {
    interest_str = '_rho';
    equip_plot.attributes.renderers[0].axis_label = 'Cost of capital'
    struc_plot.attributes.renderers[0].axis_label = 'Cost of capital'
    interest_title = 'Cost of Capital'
} else if (interest_button == 3) {
    interest_str = '_z';
    equip_plot.attributes.renderers[0].axis_label =
        'Net present value of depreciation'
    struc_plot.attributes.renderers[0].axis_label =
        'Net present value of depreciation'
    interest_title = 'Net Present Value of Depreciation'
}

equip_plot.title.text = interest_title + ' on ' + c_pt_title +
    ' Investments in Equipment';
struc_plot.title.text = interest_title + ' on ' + c_pt_title +
    ' Investments in Structures';

var new_equip_data = eval(format_str + 'equipment' + interest_str +
    type_str + c_pt_str).data
var new_struc_data = eval(format_str + 'structure' + interest_str +
    type_str + c_pt_str).data

equip_data['size'] = []
equip_data['rate'] = []
equip_data['hover'] = []
equip_data['short_category'] = []
for (var i = 0; i < new_equip_data['size'].length; i++) {
    equip_data['size'].push(new_equip_data['size' + c_pt_str][i]);
    equip_data['rate'].push(new_equip_data['rate'][i]);
    equip_data['hover'].push(new_equip_data['hover'][i]);
    equip_data['short_category'].push(new_equip_data['short_category'][i]);
}

struc_data['size'] = []
struc_data['rate'] = []
struc_data['hover'] = []
struc_data['short_category'] = []
for (var i = 0; i < new_struc_data['size'].length; i++) {
    struc_data['size'].push(new_struc_data['size'][i]);
    struc_data['rate'].push(new_struc_data['rate'][i]);
    struc_data['hover'].push(new_struc_data['hover'][i]);
    struc_data['short_category'].push(new_struc_data['short_category'][i]);
}

equip_source.change.emit();
struc_source.change.emit();
"""
