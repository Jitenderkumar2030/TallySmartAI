import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

class MobileOptimizedComponents:
    @staticmethod
    def mobile_metric_cards(metrics_data):
        """Create mobile-optimized metric cards"""
        # Use columns for mobile layout
        cols = st.columns(2)
        
        for i, (key, value) in enumerate(metrics_data.items()):
            with cols[i % 2]:
                st.metric(
                    label=key.replace('_', ' ').title(),
                    value=value,
                    delta=None
                )
    
    @staticmethod
    def mobile_chart(df, chart_type="line", height=300):
        """Create mobile-optimized charts"""
        fig = go.Figure()
        
        if chart_type == "line":
            fig.add_trace(go.Scatter(
                x=df.index,
                y=df.values,
                mode='lines+markers',
                line=dict(width=3),
                marker=dict(size=6)
            ))
        
        # Mobile-optimized layout
        fig.update_layout(
            height=height,
            margin=dict(l=20, r=20, t=40, b=20),
            font=dict(size=12),
            showlegend=False,
            xaxis=dict(
                tickangle=45,
                tickfont=dict(size=10)
            ),
            yaxis=dict(
                tickfont=dict(size=10)
            )
        )
        
        return fig
    
    @staticmethod
    def mobile_data_table(df, max_rows=10):
        """Create mobile-optimized data table"""
        if len(df) > max_rows:
            st.info(f"Showing first {max_rows} rows of {len(df)} total rows")
            df_display = df.head(max_rows)
        else:
            df_display = df
        
        # Format for mobile display
        st.dataframe(
            df_display,
            use_container_width=True,
            height=300
        )
        
        if len(df) > max_rows:
            if st.button("Show All Rows"):
                st.dataframe(df, use_container_width=True)
    
    @staticmethod
    def mobile_file_uploader(label, accepted_types):
        """Mobile-optimized file uploader"""
        uploaded_file = st.file_uploader(
            label,
            type=accepted_types,
            help="Tap to select file from your device"
        )
        
        if uploaded_file:
            file_details = {
                "Filename": uploaded_file.name,
                "File size": f"{uploaded_file.size / 1024:.1f} KB",
                "File type": uploaded_file.type
            }
            
            with st.expander("File Details"):
                for key, value in file_details.items():
                    st.write(f"**{key}:** {value}")
        
        return uploaded_file

mobile_components = MobileOptimizedComponents()