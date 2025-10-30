"""
Video Validator & Converter for WhatsApp API
A Dash-based web application for validating and converting video files
"""
import os
import base64
import io
from pathlib import Path

import dash
from dash import dcc, html, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate

from video_validator import VideoValidator, format_validation_report
from video_converter import VideoConverter


# Initialize Dash app
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME],
    title="Video Validator - WhatsApp API"
)

# Create uploads directory if it doesn't exist
UPLOAD_FOLDER = Path('uploads')
UPLOAD_FOLDER.mkdir(exist_ok=True)

# App layout
app.layout = dbc.Container([
    # Header
    dbc.Row([
        dbc.Col([
            html.H1([
                html.I(className="fas fa-video me-3"),
                "Video Validator & Converter"
            ], className="text-center my-4 text-primary"),
            html.P(
                "Validate and convert videos for WhatsApp API compliance",
                className="text-center text-muted mb-4"
            ),
        ])
    ]),

    # Main content
    dbc.Row([
        # Left column - Upload and controls
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.I(className="fas fa-upload me-2"),
                    "Upload Video"
                ], className="fw-bold"),
                dbc.CardBody([
                    # File upload
                    dcc.Upload(
                        id='upload-video',
                        children=html.Div([
                            html.I(className="fas fa-cloud-upload-alt fa-3x mb-3"),
                            html.P('Drag and Drop or Click to Select Video File'),
                            html.Small('Supported formats: MP4, 3GP, MOV, AVI, MKV', className='text-muted')
                        ]),
                        style={
                            'width': '100%',
                            'height': '200px',
                            'lineHeight': '60px',
                            'borderWidth': '2px',
                            'borderStyle': 'dashed',
                            'borderRadius': '10px',
                            'textAlign': 'center',
                            'padding': '40px',
                            'cursor': 'pointer',
                            'backgroundColor': '#f8f9fa'
                        },
                        multiple=False
                    ),

                    html.Div(id='upload-status', className='mt-3'),

                    html.Hr(),

                    # Action buttons
                    html.Div([
                        dbc.Button([
                            html.I(className="fas fa-check-circle me-2"),
                            "Validate Video"
                        ], id='validate-btn', color='primary', className='w-100 mb-2', disabled=True),

                        dbc.Button([
                            html.I(className="fas fa-sync-alt me-2"),
                            "Fix & Convert Video"
                        ], id='convert-btn', color='success', className='w-100 mb-2', disabled=True),

                        dbc.Button([
                            html.I(className="fas fa-magic me-2"),
                            "Quick Fix (moov atom only)"
                        ], id='quickfix-btn', color='warning', className='w-100 mb-2', disabled=True),
                    ]),

                    # Hidden div to store file path
                    html.Div(id='stored-filepath', style={'display': 'none'}),
                ]),
            ], className='shadow-sm mb-4'),

            # Requirements card
            dbc.Card([
                dbc.CardHeader([
                    html.I(className="fas fa-list-check me-2"),
                    "WhatsApp API Requirements"
                ], className="fw-bold"),
                dbc.CardBody([
                    html.Ul([
                        html.Li([html.Strong("Video Codec: "), "H.264 (Baseline or Main profile)"]),
                        html.Li([html.Strong("Codec Level: "), "3.0 (max 3.1)"]),
                        html.Li([html.Strong("Audio Codec: "), "AAC-LC"]),
                        html.Li([html.Strong("Container: "), "MP4 or 3GP"]),
                        html.Li([html.Strong("Max Size: "), "16 MB"]),
                        html.Li([html.Strong("Audio Streams: "), "Single or none"]),
                        html.Li([html.Strong("Pixel Format: "), "yuv420p"]),
                        html.Li([html.Strong("Progressive: "), "moov atom at beginning"]),
                    ], className='mb-0 small')
                ])
            ], className='shadow-sm')
        ], md=4),

        # Right column - Results
        dbc.Col([
            # Validation results
            html.Div(id='validation-results'),

            # Conversion results
            html.Div(id='conversion-results'),
        ], md=8),
    ]),

    # Footer
    dbc.Row([
        dbc.Col([
            html.Hr(),
            html.P([
                "Built with Dash & FFmpeg | ",
                html.A("GitHub", href="https://github.com", className="text-decoration-none")
            ], className="text-center text-muted small")
        ])
    ], className="mt-5"),

], fluid=True, className="py-4")


@app.callback(
    [Output('upload-status', 'children'),
     Output('stored-filepath', 'children'),
     Output('validate-btn', 'disabled'),
     Output('convert-btn', 'disabled'),
     Output('quickfix-btn', 'disabled')],
    Input('upload-video', 'contents'),
    State('upload-video', 'filename'),
    prevent_initial_call=True
)
def handle_upload(contents, filename):
    """Handle video file upload"""
    if contents is None:
        raise PreventUpdate

    try:
        # Decode and save file
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)

        # Save to uploads folder
        filepath = UPLOAD_FOLDER / filename
        with open(filepath, 'wb') as f:
            f.write(decoded)

        file_size_mb = len(decoded) / (1024 * 1024)

        status = dbc.Alert([
            html.I(className="fas fa-check-circle me-2"),
            f"Uploaded: {filename} ({file_size_mb:.2f} MB)"
        ], color='success')

        return status, str(filepath), False, False, False

    except Exception as e:
        status = dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Upload failed: {str(e)}"
        ], color='danger')

        return status, '', True, True, True


@app.callback(
    Output('validation-results', 'children'),
    Input('validate-btn', 'n_clicks'),
    State('stored-filepath', 'children'),
    prevent_initial_call=True
)
def validate_video(n_clicks, filepath):
    """Validate video against WhatsApp API requirements"""
    if not n_clicks or not filepath:
        raise PreventUpdate

    try:
        # Run validation
        validator = VideoValidator(filepath)
        results = validator.validate_all()

        # Create results card
        return create_validation_card(results)

    except Exception as e:
        return dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Validation error: {str(e)}"
        ], color='danger')


@app.callback(
    Output('conversion-results', 'children'),
    [Input('convert-btn', 'n_clicks'),
     Input('quickfix-btn', 'n_clicks')],
    State('stored-filepath', 'children'),
    prevent_initial_call=True
)
def convert_video(convert_clicks, quickfix_clicks, filepath):
    """Convert or fix video"""
    if not filepath:
        raise PreventUpdate

    # Determine which button was clicked
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    try:
        # Generate output path
        input_file = Path(filepath)
        output_path = UPLOAD_FOLDER / f"{input_file.stem}_fixed.mp4"

        converter = VideoConverter(filepath, str(output_path))

        # Perform conversion or quick fix
        if button_id == 'quickfix-btn':
            result = converter.fix_moov_atom()
            action = "Quick Fix (moov atom)"
        else:
            result = converter.convert()
            action = "Full Conversion"

        # Create result card
        if result['success']:
            # Validate the converted file
            validator = VideoValidator(result['output_path'])
            validation_results = validator.validate_all()

            card = dbc.Card([
                dbc.CardHeader([
                    html.I(className="fas fa-check-circle me-2"),
                    f"{action} - Success"
                ], className="bg-success text-white fw-bold"),
                dbc.CardBody([
                    html.P(result['message'], className='mb-3'),

                    dbc.Alert([
                        html.I(className="fas fa-download me-2"),
                        f"Download: {os.path.basename(result['output_path'])}"
                    ], color='info'),

                    html.Hr(),
                    html.H5("Validation Results:", className='mb-3'),
                    create_validation_table(validation_results)
                ])
            ], className='shadow-sm mb-3')

            return card
        else:
            return dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                html.Strong(f"{action} Failed: "),
                html.Br(),
                result['message']
            ], color='danger')

    except Exception as e:
        return dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Conversion error: {str(e)}"
        ], color='danger')


def create_validation_card(results):
    """Create a card displaying validation results"""
    # Determine overall status
    if results['is_valid']:
        status_color = 'success'
        status_icon = 'fa-check-circle'
        status_text = 'Video is WhatsApp API Compliant'
    else:
        status_color = 'danger'
        status_icon = 'fa-times-circle'
        status_text = 'Video Does Not Meet Requirements'

    card = dbc.Card([
        dbc.CardHeader([
            html.I(className=f"fas {status_icon} me-2"),
            "Validation Results"
        ], className=f"bg-{status_color} text-white fw-bold"),
        dbc.CardBody([
            # Overall status
            dbc.Alert([
                html.I(className=f"fas {status_icon} me-2"),
                html.Strong(status_text)
            ], color=status_color, className='mb-4'),

            # File info
            dbc.Row([
                dbc.Col([
                    html.Strong("File: "),
                    html.Span(os.path.basename(results['file_path']))
                ], md=6),
                dbc.Col([
                    html.Strong("Size: "),
                    html.Span(f"{results['file_size_mb']} MB")
                ], md=6),
            ], className='mb-3'),

            html.Hr(),

            # Validation table
            create_validation_table(results)
        ])
    ], className='shadow-sm mb-3')

    return card


def create_validation_table(results):
    """Create a table of validation details"""
    rows = []

    for name, validation in results['validations'].items():
        if validation['valid']:
            icon = html.I(className="fas fa-check-circle text-success")
            row_class = "table-success"
        else:
            icon = html.I(className="fas fa-times-circle text-danger")
            row_class = "table-danger"

        rows.append(
            html.Tr([
                html.Td(icon, style={'width': '40px'}),
                html.Td(html.Strong(name)),
                html.Td(validation['message']),
            ], className=row_class)
        )

    table = dbc.Table([
        html.Tbody(rows)
    ], bordered=True, hover=True, responsive=True, className='mb-3')

    # Add warnings if any
    warnings_section = []
    if results.get('warnings'):
        warnings_section = [
            html.Hr(),
            html.H6([
                html.I(className="fas fa-exclamation-triangle text-warning me-2"),
                "Warnings:"
            ]),
            html.Ul([
                html.Li(warning, className='text-warning') for warning in results['warnings']
            ])
        ]

    return html.Div([table] + warnings_section)


if __name__ == '__main__':
    print("\n" + "="*60)
    print("Video Validator & Converter for WhatsApp API")
    print("="*60)
    print("\nStarting server...")
    print("Open your browser and navigate to: http://127.0.0.1:8050")
    print("\nPress Ctrl+C to stop the server")
    print("="*60 + "\n")

    app.run_server(debug=True, host='127.0.0.1', port=8050)
