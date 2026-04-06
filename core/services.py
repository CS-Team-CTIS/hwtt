from io import StringIO

import pandas as pd
import plotly.express as px
from scipy.signal import savgol_filter
import numpy as np

from core.models import TestFileType, TestResults, TestRun, TestRunStatus

FILE_TYPE_COLUMNS = {
    TestFileType.TROXLER: None,   # format unknown — stub
    TestFileType.PTI: None,        # format unknown — stub
    TestFileType.CUSTOM: None,     # detected dynamically at parse time
}


class ValidateFileService:

    @staticmethod
    def _detect_encoding(raw_bytes: bytes) -> str:
        if raw_bytes.startswith(b'\xff\xfe\x00\x00'):
            return 'utf-32-le'
        elif raw_bytes.startswith(b'\x00\x00\xfe\xff'):
            return 'utf-32-be'
        elif raw_bytes.startswith(b'\xff\xfe'):
            return 'utf-16-le'
        elif raw_bytes.startswith(b'\xfe\xff'):
            return 'utf-16-be'
        elif raw_bytes.startswith(b'\xef\xbb\xbf'):
            return 'utf-8-sig'
        return 'utf-8'

    @staticmethod
    def validate_csv(file):
        import io

        file.seek(0)
        raw = file.read(4)
        encoding = ValidateFileService._detect_encoding(raw)
        file.seek(0)
        df = pd.read_csv(io.TextIOWrapper(file, encoding=encoding))
        print(df.shape)

        headers = df.columns.tolist()

        return {
            'rows' : df.shape[0],
            'cols' : df.shape[1],
            'headers' : headers[0:10],
            'valid' : True
        }

    @staticmethod
    def _parse_instrotek_sections(filepath):
        sections = {}
        current_section = None
        lines = []

        with open(filepath, 'rb') as f:
            encoding = ValidateFileService._detect_encoding(f.read(4))
        with open(filepath, 'r', encoding=encoding) as f:
            for line in f:
                line = line.strip()
                if line.startswith('[') and line.endswith(']'):
                    if current_section:
                        sections[current_section] = lines
                    current_section = line[1:-1]  # strip brackets
                    lines = []
                elif line:
                    lines.append(line)
            if current_section:
                sections[current_section] = lines

        return sections

    @staticmethod
    def _parse_instrotek(filepath):
        parsed = ValidateFileService._parse_instrotek_sections(filepath)
        graph_text = '\n'.join(parsed['GRAPH'])
        df = pd.read_csv(StringIO(graph_text), sep='\t', header=0)

        # Detect which wheel column is present (left or right)
        passes_col = next(
            (c for c in df.columns if c.startswith('Passes -')),
            None,
        )
        if passes_col is None:
            raise ValueError("No 'Passes' column found in Instrotek GRAPH section")

        col_map = {
            'passes': passes_col,
            'rut_depth': 'Rut depth [mm]',
            'temperature': 'Temperature [°C]',
        }
        return df, col_map

    @staticmethod
    def _parse_troxler(filepath):
        raise NotImplementedError("Troxler format parser not yet implemented")

    @staticmethod
    def _parse_pti(filepath):
        raise NotImplementedError("PTI format parser not yet implemented")

    @staticmethod
    def _parse_custom(filepath):
        df = pd.read_csv(filepath)
        col_map = ValidateFileService._detect_columns(df)
        return df, col_map

    @staticmethod
    def _detect_columns(df) -> dict:
        KEYWORDS = {
            'passes': ['pass', 'wheel', 'cycle'],
            'rut_depth': ['rut', 'depth', 'mm'],
            'temperature': ['temp', '°c', 'celsius'],
        }
        mapping = {}
        for canonical, keywords in KEYWORDS.items():
            for col in df.columns:
                col_lower = col.lower()
                if any(kw in col_lower for kw in keywords):
                    mapping[canonical] = col
                    break
        return mapping


class AnalysisRunService:

    @staticmethod
    def _load_dataframe(filepath, file_type):
        dispatch = {
            TestFileType.INSTROTEK: ValidateFileService._parse_instrotek,
            TestFileType.TROXLER:   ValidateFileService._parse_troxler,
            TestFileType.PTI:       ValidateFileService._parse_pti,
            TestFileType.CUSTOM:    ValidateFileService._parse_custom,
        }

        parser = dispatch.get(file_type)

        if parser is None:
            raise ValueError(f"Unsupported file type: {file_type}")
        return parser(filepath)

    @staticmethod
    def simple_analysis(filepath, test_run_id):
        test_run = TestRun.objects.get(pk=test_run_id)
        file_type = test_run.file_type

        df, col_map = AnalysisRunService._load_dataframe(filepath, file_type)

        test_results = TestResults()
        test_results.test_run = test_run
        test_results.passes_vs_rut = AnalysisRunService._passes_vs_rut(df, col_map)
        test_results.passes_vs_rut_denoise = AnalysisRunService._passes_vs_rut_denoise(df,col_map)
        test_results.rut_depth_5000 = AnalysisRunService._rut_depth_at(df, 5000, col_map)
        test_results.rut_depth_10000 = AnalysisRunService._rut_depth_at(df, 10000, col_map)
        test_results.rut_depth_15000 = AnalysisRunService._rut_depth_at(df, 15000, col_map)
        test_results.rut_depth_20000 = AnalysisRunService._rut_depth_at(df, 20000, col_map)
        test_results.rut_depth_final = AnalysisRunService._rut_depth_at(df, -1, col_map)
        test_results.inflection_pass = AnalysisRunService._sip(df, col_map)
        test_results.passes_total = AnalysisRunService._passes_total(df, col_map)

        test_run.status = TestRunStatus.COMPLETED
        test_run.save()
        test_results.save()

        return 1

    @staticmethod
    def _passes_vs_rut(df, col_map):
        fig = px.line(df, x=col_map['passes'], y=col_map['rut_depth'], title='Rut Depth vs. Number of Passes')
        return fig.to_json()

    @staticmethod
    def _passes_vs_rut_denoise(df, col_map):
        passes_col = col_map['passes']
        rut_col = col_map['rut_depth']


        def fix_spikes(df, column, min_jump_height=0.3, window=8):
            rut = df[column].astype(float).copy()
            values = rut.to_numpy(copy=True)
            n = len(values)
            i = window
            while i < n - window:
                before = np.median(values[i - window: i])
                after = np.median(values[i: i + window])
                step = after - before
                if step >= min_jump_height:
                    values[i:] -= step
                    i += window
                else:
                    i += 1
            rut.iloc[:] = values
            return rut

        def fix_negative_drops(df, column):
            rut = df[column].astype(float).copy()
            for i in range(1, len(rut)):
                if rut.iloc[i] < rut.iloc[i - 1] - 0.05:
                    drop_start = i - 1
                    pre_drop_val = rut.iloc[drop_start]
                    recovery_idx = None
                    for j in range(i, len(rut)):
                        if rut.iloc[j] >= pre_drop_val:
                            recovery_idx = j
                            break
                    if recovery_idx is not None:
                        rut.iloc[drop_start + 1: recovery_idx] = np.nan
            rut = rut.interpolate(method='linear')
            return rut


        df['rut_corrected'] = fix_negative_drops(df, rut_col)
        df['rut_corrected'] = fix_spikes(df, 'rut_corrected')
        df['rut_depth_smooth'] = savgol_filter(df['rut_corrected'].values, 701, 3)


        fig = px.line(df, x=passes_col, y="rut_depth_smooth", title='Rut Depth vs. Number of Passes Denoised')
        fig.show()
        return fig.to_json()

    @staticmethod
    def _sip(df, col_map):
        passes_col = col_map['passes']
        rut_col = 'rut_depth_smooth'

        df['slope'] = df[rut_col].diff() / df[passes_col].diff()
        df['slope_change'] = df['slope'].diff()

        sip_idx = df['slope'].idxmin()
        sip = df.loc[sip_idx, passes_col]

        print(sip_idx, sip)
        return sip

    @staticmethod
    def _passes_total(df, col_map):
        return df.iloc[-1][col_map['passes']]

    @staticmethod
    def _rut_depth_at(df, target_passes, col_map):
        passes_col = col_map['passes']
        rut_col = 'rut_depth_smooth'

        if target_passes == -1:
            return df[rut_col].iloc[-1]

        row = df[df[passes_col] == target_passes]

        if row.empty:
            return None  # test ended before reaching target passes

        return row[rut_col].iloc[0]
