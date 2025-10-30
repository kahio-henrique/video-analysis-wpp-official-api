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
from translations import TRANSLATIONS, get_text


# Initialize Dash app
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME],
    title="Video Validator - WhatsApp API"
)

# Create uploads directory if it doesn't exist
UPLOAD_FOLDER = Path('uploads')
UPLOAD_FOLDER.mkdir(exist_ok=True)

# App layout with minimalist design
app.layout = dbc.Container([
    # Language store
    dcc.Store(id='language-store', data='en'),

    # Header with language selector
    dbc.Row([
        dbc.Col([
            html.Div([
                # Language selector (top right)
                html.Div([
                    dcc.Dropdown(
                        id='language-selector',
                        options=[
                            {'label': '🇺🇸 English', 'value': 'en'},
                            {'label': '🇧🇷 Português', 'value': 'pt'},
                            {'label': '🇪🇸 Español', 'value': 'es'}
                        ],
                        value='en',
                        clearable=False,
                        searchable=False,
                        style={
                            'width': '160px',
                            'fontSize': '0.85rem',
                            'border': 'none'
                        }
                    )
                ], style={'position': 'absolute', 'top': '1rem', 'right': '1rem'}),

                # Title
                html.H1(id='page-title', className="text-center mb-2",
                       style={'fontWeight': '300', 'fontSize': '2.5rem', 'color': '#1a1a1a'}),
                html.P(
                    id='page-subtitle',
                    className="text-center mb-5",
                    style={'color': '#666', 'fontSize': '0.95rem', 'letterSpacing': '0.5px'}
                ),
            ], style={'marginTop': '3rem', 'position': 'relative'})
        ])
    ]),

    # Main content
    dbc.Row([
        # Left column - Upload and controls
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    # File upload
                    dcc.Upload(
                        id='upload-video',
                        children=html.Div([
                            html.Div("📁", style={'fontSize': '3rem', 'marginBottom': '1rem'}),
                            html.P(id='upload-title', style={'marginBottom': '0.5rem', 'color': '#333', 'fontSize': '1rem'}),
                            html.Small(id='upload-subtitle', style={'color': '#999', 'fontSize': '0.85rem'})
                        ]),
                        style={
                            'width': '100%',
                            'height': '180px',
                            'borderWidth': '2px',
                            'borderStyle': 'dashed',
                            'borderRadius': '8px',
                            'borderColor': '#ddd',
                            'textAlign': 'center',
                            'padding': '40px',
                            'cursor': 'pointer',
                            'backgroundColor': '#fafafa',
                            'display': 'flex',
                            'alignItems': 'center',
                            'justifyContent': 'center',
                            'transition': 'all 0.2s ease'
                        },
                        multiple=False
                    ),

                    html.Div(id='upload-status', className='mt-3'),

                    html.Hr(),

                    # Action buttons
                    html.Div([
                        dbc.Button(
                            "Validate",
                            id='validate-btn',
                            className='w-100 mb-2',
                            disabled=True,
                            style={
                                'backgroundColor': '#1a1a1a',
                                'border': 'none',
                                'borderRadius': '6px',
                                'padding': '0.75rem',
                                'fontSize': '0.9rem',
                                'fontWeight': '400',
                                'letterSpacing': '0.3px'
                            }
                        ),

                        dbc.Button(
                            "Convert & Fix",
                            id='convert-btn',
                            className='w-100 mb-2',
                            disabled=True,
                            style={
                                'backgroundColor': '#2a2a2a',
                                'border': 'none',
                                'borderRadius': '6px',
                                'padding': '0.75rem',
                                'fontSize': '0.9rem',
                                'fontWeight': '400',
                                'letterSpacing': '0.3px'
                            }
                        ),

                        html.Div([
                            dbc.Button(
                                [
                                    html.Div("Quick Fix", style={'marginBottom': '0.15rem'}),
                                    html.Small("(moov atom only)", style={'fontSize': '0.75rem', 'opacity': '0.7'})
                                ],
                                id='quickfix-btn',
                                className='w-100 mb-2',
                                disabled=True,
                                style={
                                    'backgroundColor': '#fff',
                                    'color': '#333',
                                    'border': '1px solid #ddd',
                                    'borderRadius': '6px',
                                    'padding': '0.75rem',
                                    'fontSize': '0.9rem',
                                    'fontWeight': '400',
                                    'letterSpacing': '0.3px'
                                }
                            ),
                        ]),
                    ]),

                    # Info about output location
                    html.Div([
                        html.P([
                            html.Small("Output: ", style={'color': '#999', 'fontSize': '0.8rem'}),
                            html.Small("uploads/", style={'color': '#666', 'fontSize': '0.8rem', 'fontFamily': 'monospace'})
                        ], className='mb-0 mt-3', style={'textAlign': 'center'})
                    ]),

                    # Hidden div to store file path
                    html.Div(id='stored-filepath', style={'display': 'none'}),
                ]),
            ], style={'border': '1px solid #e0e0e0', 'borderRadius': '8px', 'boxShadow': 'none'}, className='mb-4'),

            # Requirements card
            dbc.Card([
                dbc.CardBody([
                    html.H6("WhatsApp API Requirements", style={'fontSize': '0.95rem', 'fontWeight': '400', 'color': '#333', 'marginBottom': '1rem'}),
                    html.Div([
                        # Video Codec
                        html.Div([
                            html.Div("Video Codec", style={'fontSize': '0.75rem', 'color': '#999', 'textTransform': 'uppercase', 'letterSpacing': '0.5px', 'marginBottom': '0.25rem'}),
                            html.Div("H.264 (Baseline or Main profile)", style={'fontSize': '0.85rem', 'color': '#333', 'marginBottom': '0.75rem'}),
                        ]),
                        # Codec Level
                        html.Div([
                            html.Div("Codec Level", style={'fontSize': '0.75rem', 'color': '#999', 'textTransform': 'uppercase', 'letterSpacing': '0.5px', 'marginBottom': '0.25rem'}),
                            html.Div("3.0 (max 3.1)", style={'fontSize': '0.85rem', 'color': '#333', 'marginBottom': '0.75rem'}),
                        ]),
                        # Audio Codec
                        html.Div([
                            html.Div("Audio Codec", style={'fontSize': '0.75rem', 'color': '#999', 'textTransform': 'uppercase', 'letterSpacing': '0.5px', 'marginBottom': '0.25rem'}),
                            html.Div("AAC-LC", style={'fontSize': '0.85rem', 'color': '#333', 'marginBottom': '0.75rem'}),
                        ]),
                        # Container
                        html.Div([
                            html.Div("Container", style={'fontSize': '0.75rem', 'color': '#999', 'textTransform': 'uppercase', 'letterSpacing': '0.5px', 'marginBottom': '0.25rem'}),
                            html.Div("MP4 or 3GP", style={'fontSize': '0.85rem', 'color': '#333', 'marginBottom': '0.75rem'}),
                        ]),
                        # File Size
                        html.Div([
                            html.Div("Max Size", style={'fontSize': '0.75rem', 'color': '#999', 'textTransform': 'uppercase', 'letterSpacing': '0.5px', 'marginBottom': '0.25rem'}),
                            html.Div("16 MB", style={'fontSize': '0.85rem', 'color': '#333', 'marginBottom': '0.75rem'}),
                        ]),
                        # Audio Streams
                        html.Div([
                            html.Div("Audio Streams", style={'fontSize': '0.75rem', 'color': '#999', 'textTransform': 'uppercase', 'letterSpacing': '0.5px', 'marginBottom': '0.25rem'}),
                            html.Div("Single or none", style={'fontSize': '0.85rem', 'color': '#333', 'marginBottom': '0.75rem'}),
                        ]),
                        # Pixel Format
                        html.Div([
                            html.Div("Pixel Format", style={'fontSize': '0.75rem', 'color': '#999', 'textTransform': 'uppercase', 'letterSpacing': '0.5px', 'marginBottom': '0.25rem'}),
                            html.Div("yuv420p", style={'fontSize': '0.85rem', 'color': '#333', 'marginBottom': '0.75rem'}),
                        ]),
                        # Progressive
                        html.Div([
                            html.Div("Progressive", style={'fontSize': '0.75rem', 'color': '#999', 'textTransform': 'uppercase', 'letterSpacing': '0.5px', 'marginBottom': '0.25rem'}),
                            html.Div("moov atom at beginning", style={'fontSize': '0.85rem', 'color': '#333'}),
                        ]),
                    ])
                ])
            ], style={'border': '1px solid #e0e0e0', 'borderRadius': '8px', 'boxShadow': 'none'})
        ], md=4),

        # Right column - Results
        dbc.Col([
            # Validation results
            dcc.Loading(
                id="loading-validation",
                type="default",
                children=html.Div(id='validation-results')
            ),

            # Conversion results
            dcc.Loading(
                id="loading-conversion",
                type="default",
                children=html.Div(id='conversion-results')
            ),
        ], md=8),
    ]),

    # Footer
    dbc.Row([
        dbc.Col([
            html.Div(
                style={'borderTop': '1px solid #e0e0e0', 'marginTop': '4rem', 'paddingTop': '2rem', 'paddingBottom': '2rem'}
            ),
            html.P([
                html.Span("Built with Dash & FFmpeg", style={'color': '#999', 'fontSize': '0.85rem'}),
                html.Span(" • ", style={'color': '#ddd', 'margin': '0 0.5rem'}),
                html.A("GitHub",
                       href="https://github.com/kahio-henrique/video-analysis-wpp-official-api",
                       target="_blank",
                       style={'color': '#666', 'fontSize': '0.85rem', 'textDecoration': 'none', 'borderBottom': '1px solid #ddd'})
            ], className="text-center")
        ])
    ]),

], fluid=True, style={'maxWidth': '1200px', 'padding': '2rem'})


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

        status = html.Div([
            html.Div("✓ Upload Complete", style={
                'backgroundColor': '#f1f8f4',
                'color': '#4CAF50',
                'padding': '0.75rem 1rem',
                'borderRadius': '6px',
                'fontSize': '0.85rem',
                'fontWeight': '400',
                'marginBottom': '0.5rem'
            }),
            html.Div(f"{filename} • {file_size_mb:.2f} MB", style={
                'color': '#666',
                'fontSize': '0.8rem',
                'padding': '0.25rem 0'
            })
        ])

        return status, str(filepath), False, False, False

    except Exception as e:
        status = html.Div([
            html.Div("✗ Upload Failed", style={
                'backgroundColor': '#fef2f2',
                'color': '#f44336',
                'padding': '0.75rem 1rem',
                'borderRadius': '6px',
                'fontSize': '0.85rem',
                'fontWeight': '400',
                'marginBottom': '0.5rem'
            }),
            html.Div(str(e), style={
                'color': '#666',
                'fontSize': '0.8rem',
                'padding': '0.25rem 0'
            })
        ])

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
        return html.Div([
            html.Div("✗ Validation Error", style={
                'backgroundColor': '#fef2f2',
                'color': '#f44336',
                'padding': '1rem 1.5rem',
                'borderRadius': '6px',
                'fontSize': '0.95rem',
                'fontWeight': '400',
                'marginBottom': '0.5rem',
                'borderLeft': '3px solid #f44336'
            }),
            html.Div(str(e), style={
                'color': '#666',
                'fontSize': '0.85rem',
                'padding': '0.5rem 0'
            })
        ])


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
                dbc.CardBody([
                    # Success badge
                    html.Div([
                        html.Div(f"✓ {action} Complete", style={
                            'backgroundColor': '#f1f8f4',
                            'color': '#4CAF50',
                            'padding': '0.75rem 1.5rem',
                            'borderRadius': '6px',
                            'display': 'inline-block',
                            'fontSize': '0.95rem',
                            'fontWeight': '400',
                            'letterSpacing': '0.3px',
                            'marginBottom': '1.5rem'
                        })
                    ]),

                    # File location
                    html.Div([
                        html.Div("Output File", style={'fontSize': '0.8rem', 'color': '#999', 'marginBottom': '0.5rem'}),
                        html.Code(
                            os.path.basename(result['output_path']),
                            style={
                                'display': 'block',
                                'padding': '0.75rem',
                                'backgroundColor': '#fafafa',
                                'color': '#333',
                                'fontSize': '0.85rem',
                                'borderRadius': '6px',
                                'border': '1px solid #e0e0e0',
                                'fontFamily': 'monospace'
                            }
                        ),
                        html.Small(
                            f"Location: {str(UPLOAD_FOLDER.absolute())}",
                            style={'color': '#999', 'fontSize': '0.75rem', 'display': 'block', 'marginTop': '0.5rem'}
                        )
                    ], style={'marginBottom': '1.5rem'}),

                    # File size
                    html.Div(
                        f"Size: {os.path.getsize(result['output_path']) / (1024 * 1024):.2f} MB",
                        style={'color': '#666', 'fontSize': '0.85rem', 'marginBottom': '1.5rem'}
                    ),

                    html.Hr(style={'borderColor': '#e0e0e0', 'margin': '1.5rem 0'}),

                    html.H6("Validation Results", style={'fontSize': '0.9rem', 'fontWeight': '400', 'color': '#666', 'marginBottom': '1rem'}),
                    create_validation_table(validation_results)
                ])
            ], style={'border': '1px solid #e0e0e0', 'borderRadius': '8px', 'boxShadow': 'none'}, className='mb-3')

            return card
        else:
            return html.Div([
                html.Div(f"✗ {action} Failed", style={
                    'backgroundColor': '#fef2f2',
                    'color': '#f44336',
                    'padding': '1rem 1.5rem',
                    'borderRadius': '6px',
                    'fontSize': '0.95rem',
                    'fontWeight': '400',
                    'marginBottom': '0.5rem',
                    'borderLeft': '3px solid #f44336'
                }),
                html.Div(result['message'], style={
                    'color': '#666',
                    'fontSize': '0.85rem',
                    'padding': '0.5rem 0'
                })
            ])

    except Exception as e:
        return html.Div([
            html.Div("✗ Conversion Error", style={
                'backgroundColor': '#fef2f2',
                'color': '#f44336',
                'padding': '1rem 1.5rem',
                'borderRadius': '6px',
                'fontSize': '0.95rem',
                'fontWeight': '400',
                'marginBottom': '0.5rem',
                'borderLeft': '3px solid #f44336'
            }),
            html.Div(str(e), style={
                'color': '#666',
                'fontSize': '0.85rem',
                'padding': '0.5rem 0'
            })
        ])


def create_validation_card(results):
    """Create a card displaying validation results"""
    # Determine overall status
    if results['is_valid']:
        status_color = '#4CAF50'
        status_bg = '#f1f8f4'
        status_text = '✓ Valid'
    else:
        status_color = '#f44336'
        status_bg = '#fef2f2'
        status_text = '✗ Invalid'

    card = dbc.Card([
        dbc.CardBody([
            # Overall status
            html.Div([
                html.Div(status_text, style={
                    'backgroundColor': status_bg,
                    'color': status_color,
                    'padding': '0.75rem 1.5rem',
                    'borderRadius': '6px',
                    'display': 'inline-block',
                    'fontSize': '0.95rem',
                    'fontWeight': '400',
                    'letterSpacing': '0.3px',
                    'marginBottom': '1.5rem'
                })
            ]),

            # File info
            html.Div([
                html.Span(os.path.basename(results['file_path']),
                         style={'color': '#333', 'fontSize': '0.9rem', 'marginRight': '1rem'}),
                html.Span(f"{results['file_size_mb']} MB",
                         style={'color': '#999', 'fontSize': '0.85rem'})
            ], style={'marginBottom': '1.5rem'}),

            html.Hr(style={'borderColor': '#e0e0e0', 'margin': '1.5rem 0'}),

            # Validation table
            create_validation_table(results)
        ])
    ], style={'border': '1px solid #e0e0e0', 'borderRadius': '8px', 'boxShadow': 'none'}, className='mb-3')

    return card


def create_validation_table(results):
    """Create a table of validation details"""
    rows = []

    for name, validation in results['validations'].items():
        if validation['valid']:
            icon = "✓"
            icon_color = '#4CAF50'
            bg_color = '#fafafa'
        else:
            icon = "✗"
            icon_color = '#f44336'
            bg_color = '#fff'

        rows.append(
            html.Div([
                html.Div([
                    html.Span(icon, style={'color': icon_color, 'fontSize': '1rem', 'marginRight': '0.75rem'}),
                    html.Span(name, style={'color': '#333', 'fontSize': '0.9rem', 'fontWeight': '400'}),
                ], style={'marginBottom': '0.25rem'}),
                html.Div(
                    validation['message'],
                    style={'color': '#666', 'fontSize': '0.85rem', 'marginLeft': '1.5rem'}
                )
            ], style={
                'padding': '0.75rem',
                'backgroundColor': bg_color,
                'borderRadius': '6px',
                'marginBottom': '0.5rem'
            })
        )

    # Only show if there are validations
    content = []
    if rows:
        content.append(html.Div(rows))

    # Add errors if any
    if results.get('errors'):
        content.append(html.Hr(style={'borderColor': '#e0e0e0', 'margin': '1.5rem 0'}))
        content.append(html.H6("Issues Found",
                               style={'fontSize': '0.9rem', 'fontWeight': '400', 'color': '#f44336', 'marginBottom': '1rem'}))
        for error in results['errors']:
            content.append(html.Div(
                error,
                style={
                    'padding': '0.75rem',
                    'backgroundColor': '#fef2f2',
                    'color': '#666',
                    'fontSize': '0.85rem',
                    'borderRadius': '6px',
                    'marginBottom': '0.5rem',
                    'borderLeft': '3px solid #f44336'
                }
            ))

    # Add warnings if any
    if results.get('warnings'):
        content.append(html.Hr(style={'borderColor': '#e0e0e0', 'margin': '1.5rem 0'}))
        content.append(html.H6("Warnings",
                               style={'fontSize': '0.9rem', 'fontWeight': '400', 'color': '#ff9800', 'marginBottom': '1rem'}))
        for warning in results['warnings']:
            content.append(html.Div(
                warning,
                style={
                    'padding': '0.75rem',
                    'backgroundColor': '#fff8e1',
                    'color': '#666',
                    'fontSize': '0.85rem',
                    'borderRadius': '6px',
                    'marginBottom': '0.5rem',
                    'borderLeft': '3px solid #ff9800'
                }
            ))

    return html.Div(content)


# Translation callback - updates UI text when language changes
@app.callback(
    [Output('page-title', 'children'),
     Output('page-subtitle', 'children'),
     Output('upload-title', 'children'),
     Output('upload-subtitle', 'children')],
    Input('language-selector', 'value')
)
def update_translations(lang):
    """Update UI text based on selected language"""
    return (
        get_text(lang, 'title'),
        get_text(lang, 'subtitle'),
        get_text(lang, 'upload_title'),
        get_text(lang, 'upload_subtitle')
    )


if __name__ == '__main__':
    print("\n" + "="*60)
    print("Video Validator & Converter for WhatsApp API")
    print("="*60)
    print("\nStarting server...")
    print("Open your browser and navigate to: http://127.0.0.1:8050")
    print("\nPress Ctrl+C to stop the server")
    print("="*60 + "\n")

    app.run(debug=True, host='127.0.0.1', port=8050)
