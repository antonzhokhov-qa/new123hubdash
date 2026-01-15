"""Metrics schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any

from pydantic import BaseModel


class StatusMetrics(BaseModel):
    """Metrics by status."""

    count: int
    amount: Decimal
    amount_usd: Optional[Decimal] = None  # Amount in USD


class MetricsOverview(BaseModel):
    """Overview metrics for dashboard."""

    period: Dict[str, str]  # from, to
    total_count: int
    total_amount: Decimal
    total_amount_usd: Optional[Decimal] = None  # Total in USD
    currency: str = "INR"
    display_currency: str = "USD"  # For frontend display
    
    by_status: Dict[str, StatusMetrics]
    # success, failed, pending
    
    by_source: Dict[str, StatusMetrics]
    # vima, payshack
    
    conversion_rate: float  # success / total * 100
    avg_ticket: Decimal
    avg_ticket_usd: Optional[Decimal] = None  # Avg ticket in USD
    
    # Comparison with previous period
    count_change_percent: Optional[float] = None
    amount_change_percent: Optional[float] = None


class ProjectMetrics(BaseModel):
    """Metrics for a single project."""

    project: str
    total_count: int
    total_amount: Decimal
    total_amount_usd: Optional[Decimal] = None
    success_count: int
    success_amount: Decimal
    success_amount_usd: Optional[Decimal] = None
    failed_count: int
    failed_amount: Decimal
    failed_amount_usd: Optional[Decimal] = None
    conversion_rate: float


class MetricsByProject(BaseModel):
    """Metrics grouped by project."""

    period: Dict[str, str]
    projects: List[ProjectMetrics]


class MetricsByStatus(BaseModel):
    """Metrics grouped by status."""

    period: Dict[str, str]
    statuses: Dict[str, StatusMetrics]


class TrendPoint(BaseModel):
    """Single point in trend data."""

    timestamp: datetime
    count: int
    amount: Decimal
    amount_usd: Optional[Decimal] = None  # Amount in USD
    success_count: int
    failed_count: int
    pending_count: int = 0
    conversion_rate: float = 0.0  # success / total * 100


class MetricsTrend(BaseModel):
    """Trend data for charts."""

    period: Dict[str, str]
    granularity: str  # minute | 5min | 15min | hour | day
    data: List[TrendPoint]


class SourceTrendData(BaseModel):
    """Trend data for a single source."""

    source: str  # "vima" | "payshack"
    data: List[TrendPoint]
    totals: StatusMetrics


class MetricsBySource(BaseModel):
    """Metrics by source with trends."""

    period: Dict[str, str]
    granularity: str
    sources: List[SourceTrendData]


class HeatmapCell(BaseModel):
    """Single cell in heatmap."""

    x: str  # hour (0-23) or day (Mon-Sun) or merchant name
    y: str  # corresponding dimension
    value: Decimal
    count: int


class HeatmapResponse(BaseModel):
    """Heatmap data response."""

    dimension: str  # "hour_day" | "merchant_hour" | "merchant_day"
    metric: str  # "amount" | "count" | "conversion"
    x_labels: List[str]
    y_labels: List[str]
    cells: List[HeatmapCell]
    min_value: Decimal
    max_value: Decimal


class HourlyDistributionPoint(BaseModel):
    """Single point in hourly distribution heatmap."""

    day_of_week: int  # 0=Monday, 6=Sunday
    day_name: str  # Mon, Tue, etc.
    hour: int  # 0-23
    count: int
    success_count: int
    failed_count: int
    success_rate: float


class HourlyDistribution(BaseModel):
    """Hourly distribution for heatmap."""

    period: Dict[str, str]
    data: List[HourlyDistributionPoint]


class AmountBucketPoint(BaseModel):
    """Single point in amount distribution heatmap."""

    bucket: str  # "0-100", "100-500", etc.
    bucket_index: int  # for sorting
    hour: int  # 0-23
    count: int
    total_amount: Decimal


class AmountDistribution(BaseModel):
    """Amount distribution by bucket and hour."""

    period: Dict[str, str]
    buckets: List[str]  # List of bucket labels
    data: List[AmountBucketPoint]


class ConversionByProject(BaseModel):
    """Project metrics with conversion focus."""

    project: str
    total_count: int
    success_count: int
    failed_count: int
    conversion_rate: float
    avg_ticket: Decimal
    total_amount: Decimal


class ConversionByProjectResponse(BaseModel):
    """Response for conversion by project."""

    period: Dict[str, str]
    projects: List[ConversionByProject]
    top_5: List[ConversionByProject]
    bottom_5: List[ConversionByProject]


# ========== Period Comparison ==========

class PeriodMetrics(BaseModel):
    """Metrics for a single period."""

    period_name: str  # "current", "previous"
    from_date: str
    to_date: str
    total_count: int
    total_amount: Decimal
    success_count: int
    success_amount: Decimal
    failed_count: int
    conversion_rate: float
    avg_ticket: Decimal


class MetricComparison(BaseModel):
    """Comparison between two periods."""

    count_change: int
    count_change_percent: float
    amount_change: Decimal
    amount_change_percent: float
    conversion_change: float  # percentage points
    avg_ticket_change: Decimal
    avg_ticket_change_percent: float


class PeriodComparisonResponse(BaseModel):
    """Response for period comparison."""

    current: PeriodMetrics
    previous: PeriodMetrics
    comparison: MetricComparison


# ========== Country / Geo Metrics ==========

class CountryMetrics(BaseModel):
    """Metrics for a single country."""

    country: str
    country_name: str
    total_count: int
    total_amount: Decimal
    success_count: int
    failed_count: int
    conversion_rate: float
    avg_ticket: Decimal
    percentage_of_total: float  # % of total volume


class MetricsByCountry(BaseModel):
    """Metrics grouped by country."""

    period: Dict[str, str]
    countries: List[CountryMetrics]
    total_count: int
    total_amount: Decimal


# ========== Merchant Metrics ==========

class MerchantMetrics(BaseModel):
    """Detailed metrics for a single merchant."""

    merchant_id: str
    project: str
    total_count: int
    total_amount: Decimal
    success_count: int
    success_amount: Decimal
    failed_count: int
    failed_amount: Decimal
    pending_count: int
    conversion_rate: float
    avg_ticket: Decimal
    first_txn_at: Optional[datetime] = None
    last_txn_at: Optional[datetime] = None


class MerchantListResponse(BaseModel):
    """Paginated merchant list response."""

    period: Dict[str, str]
    merchants: List[MerchantMetrics]
    total: int
    page: int
    limit: int
    pages: int


class MerchantDetailResponse(BaseModel):
    """Detailed merchant analytics."""

    merchant: MerchantMetrics
    hourly_trend: List[TrendPoint]
    daily_conversion: List[Dict[str, Any]]  # date, conversion_rate


# ========== RPM (Requests/Transactions Per Minute) ==========

class RPMPoint(BaseModel):
    """Single point in RPM data."""

    timestamp: datetime
    rpm: float  # transactions per minute
    success_rpm: float
    failed_rpm: float
    avg_response_time_ms: Optional[float] = None


class RPMResponse(BaseModel):
    """RPM metrics response."""

    period: Dict[str, str]
    current_rpm: float  # Current RPM (last minute)
    avg_rpm: float  # Average RPM for period
    max_rpm: float  # Maximum RPM in period
    min_rpm: float  # Minimum RPM in period
    total_transactions: int
    data: List[RPMPoint]  # Time series data


class LiveMetrics(BaseModel):
    """Real-time live metrics."""

    timestamp: datetime
    current_rpm: float
    success_rate: float
    avg_ticket: Decimal
    pending_count: int
    last_5min_count: int
    last_5min_amount: Decimal
    last_5min_success_rate: float


# ========== Horizontal Bar Chart Data ==========

class HorizontalBarItem(BaseModel):
    """Item for horizontal bar chart."""

    label: str
    value: Decimal
    count: int
    percentage: float  # % of total


class HorizontalBarResponse(BaseModel):
    """Response for horizontal bar chart."""

    period: Dict[str, str]
    metric: str  # "volume" | "count" | "conversion"
    items: List[HorizontalBarItem]
    total: Decimal
