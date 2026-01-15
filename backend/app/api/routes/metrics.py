"""Metrics endpoints."""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, and_, case, literal
from sqlalchemy.ext.asyncio import AsyncSession
import orjson

from app.db.session import get_db
from app.db.redis import cache
from app.config import settings
from app.models.transaction import Transaction
from app.schemas.metrics import (
    MetricsOverview,
    StatusMetrics,
    MetricsByProject,
    ProjectMetrics,
    MetricsTrend,
    TrendPoint,
    HourlyDistribution,
    HourlyDistributionPoint,
    AmountDistribution,
    AmountBucketPoint,
    ConversionByProject,
    ConversionByProjectResponse,
    SourceTrendData,
    MetricsBySource,
    HeatmapCell,
    HeatmapResponse,
    PeriodMetrics,
    MetricComparison,
    PeriodComparisonResponse,
    CountryMetrics,
    MetricsByCountry,
    MerchantMetrics,
    MerchantListResponse,
    RPMPoint,
    RPMResponse,
    LiveMetrics,
    HorizontalBarItem,
    HorizontalBarResponse,
)

router = APIRouter()


@router.get("/overview", response_model=MetricsOverview)
async def get_metrics_overview(
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    source: Optional[str] = Query(None),
    project: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Get overview metrics for dashboard KPI cards.
    Cached for fast response.
    """
    # Default to last 7 days
    if not to_date:
        to_date = date.today()
    if not from_date:
        from_date = to_date - timedelta(days=7)

    # Check cache
    cache_key = f"metrics:overview:{from_date}:{to_date}:{source}:{project}"
    cached = await cache.get(cache_key)
    if cached:
        return MetricsOverview.model_validate(orjson.loads(cached))

    # Build query conditions
    conditions = [
        Transaction.created_at >= datetime.combine(from_date, datetime.min.time()),
        Transaction.created_at <= datetime.combine(to_date, datetime.max.time()),
    ]
    if source:
        conditions.append(Transaction.source == source)
    if project:
        conditions.append(Transaction.project == project)

    # Query aggregates
    query = select(
        func.count(Transaction.id).label("total_count"),
        func.coalesce(func.sum(Transaction.amount), 0).label("total_amount"),
        func.count(case((Transaction.status == "success", 1))).label("success_count"),
        func.coalesce(
            func.sum(case((Transaction.status == "success", Transaction.amount))), 0
        ).label("success_amount"),
        func.count(case((Transaction.status == "failed", 1))).label("failed_count"),
        func.coalesce(
            func.sum(case((Transaction.status == "failed", Transaction.amount))), 0
        ).label("failed_amount"),
        func.count(case((Transaction.status == "pending", 1))).label("pending_count"),
        func.coalesce(
            func.sum(case((Transaction.status == "pending", Transaction.amount))), 0
        ).label("pending_amount"),
        func.count(case((Transaction.source == "vima", 1))).label("vima_count"),
        func.coalesce(
            func.sum(case((Transaction.source == "vima", Transaction.amount))), 0
        ).label("vima_amount"),
        func.count(case((Transaction.source == "payshack", 1))).label("payshack_count"),
        func.coalesce(
            func.sum(case((Transaction.source == "payshack", Transaction.amount))), 0
        ).label("payshack_amount"),
    ).where(and_(*conditions))

    result = await db.execute(query)
    row = result.one()

    total_count = row.total_count or 0
    total_amount = Decimal(str(row.total_amount or 0))
    success_count = row.success_count or 0

    conversion_rate = (success_count / total_count * 100) if total_count > 0 else 0
    avg_ticket = (total_amount / total_count) if total_count > 0 else Decimal(0)

    metrics = MetricsOverview(
        period={"from": from_date.isoformat(), "to": to_date.isoformat()},
        total_count=total_count,
        total_amount=total_amount,
        currency="INR",
        by_status={
            "success": StatusMetrics(
                count=row.success_count or 0,
                amount=Decimal(str(row.success_amount or 0)),
            ),
            "failed": StatusMetrics(
                count=row.failed_count or 0,
                amount=Decimal(str(row.failed_amount or 0)),
            ),
            "pending": StatusMetrics(
                count=row.pending_count or 0,
                amount=Decimal(str(row.pending_amount or 0)),
            ),
        },
        by_source={
            "vima": StatusMetrics(
                count=row.vima_count or 0,
                amount=Decimal(str(row.vima_amount or 0)),
            ),
            "payshack": StatusMetrics(
                count=row.payshack_count or 0,
                amount=Decimal(str(row.payshack_amount or 0)),
            ),
        },
        conversion_rate=round(conversion_rate, 2),
        avg_ticket=round(avg_ticket, 2),
    )

    # Cache result
    await cache.set(
        cache_key,
        orjson.dumps(metrics.model_dump(mode="json")).decode(),
        ttl=settings.cache_ttl_metrics,
    )

    return metrics


@router.get("/by-project", response_model=MetricsByProject)
async def get_metrics_by_project(
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    source: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Get metrics grouped by project."""
    if not to_date:
        to_date = date.today()
    if not from_date:
        from_date = to_date - timedelta(days=7)

    conditions = [
        Transaction.created_at >= datetime.combine(from_date, datetime.min.time()),
        Transaction.created_at <= datetime.combine(to_date, datetime.max.time()),
    ]
    if source:
        conditions.append(Transaction.source == source)

    query = (
        select(
            Transaction.project,
            func.count(Transaction.id).label("total_count"),
            func.coalesce(func.sum(Transaction.amount), 0).label("total_amount"),
            func.count(case((Transaction.status == "success", 1))).label("success_count"),
            func.coalesce(
                func.sum(case((Transaction.status == "success", Transaction.amount))), 0
            ).label("success_amount"),
            func.count(case((Transaction.status == "failed", 1))).label("failed_count"),
            func.coalesce(
                func.sum(case((Transaction.status == "failed", Transaction.amount))), 0
            ).label("failed_amount"),
        )
        .where(and_(*conditions))
        .group_by(Transaction.project)
        .order_by(func.sum(Transaction.amount).desc())
    )

    result = await db.execute(query)
    rows = result.all()

    projects = []
    for row in rows:
        total = row.total_count or 0
        success = row.success_count or 0
        projects.append(
            ProjectMetrics(
                project=row.project or "unknown",
                total_count=total,
                total_amount=Decimal(str(row.total_amount or 0)),
                success_count=success,
                success_amount=Decimal(str(row.success_amount or 0)),
                failed_count=row.failed_count or 0,
                failed_amount=Decimal(str(row.failed_amount or 0)),
                conversion_rate=round((success / total * 100) if total > 0 else 0, 2),
            )
        )

    return MetricsByProject(
        period={"from": from_date.isoformat(), "to": to_date.isoformat()},
        projects=projects,
    )


@router.get("/trends", response_model=MetricsTrend)
async def get_metrics_trends(
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    granularity: str = Query("hour", description="minute | 5min | 15min | hour | day"),
    source: Optional[str] = Query(None, description="Filter by source: vima | payshack"),
    project: Optional[str] = Query(None, description="Filter by project"),
    db: AsyncSession = Depends(get_db),
):
    """Get trend data for charts with configurable granularity."""
    if not to_date:
        to_date = date.today()
    if not from_date:
        # Default period based on granularity
        if granularity == "minute":
            from_date = to_date  # Today only for minute
        elif granularity in ("5min", "15min"):
            from_date = to_date  # Today only
        elif granularity == "hour":
            from_date = to_date - timedelta(days=1)
        else:
            from_date = to_date - timedelta(days=7)

    conditions = [
        Transaction.created_at >= datetime.combine(from_date, datetime.min.time()),
        Transaction.created_at <= datetime.combine(to_date, datetime.max.time()),
    ]
    if source:
        conditions.append(Transaction.source == source)
    if project:
        conditions.append(Transaction.project == project)

    # Group by granularity
    if granularity == "minute":
        time_group = func.date_trunc("minute", Transaction.created_at)
    elif granularity == "5min":
        # Round to 5-minute intervals: floor(extract(epoch)/300)*300
        epoch = func.extract("epoch", Transaction.created_at)
        rounded_epoch = func.floor(epoch / 300) * 300
        time_group = func.to_timestamp(rounded_epoch)
    elif granularity == "15min":
        # Round to 15-minute intervals
        epoch = func.extract("epoch", Transaction.created_at)
        rounded_epoch = func.floor(epoch / 900) * 900
        time_group = func.to_timestamp(rounded_epoch)
    elif granularity == "hour":
        time_group = func.date_trunc("hour", Transaction.created_at)
    else:  # day
        time_group = func.date_trunc("day", Transaction.created_at)

    query = (
        select(
            time_group.label("timestamp"),
            func.count(Transaction.id).label("count"),
            func.coalesce(func.sum(Transaction.amount), 0).label("amount"),
            func.count(case((Transaction.status == "success", 1))).label("success_count"),
            func.count(case((Transaction.status == "failed", 1))).label("failed_count"),
            func.count(case((Transaction.status == "pending", 1))).label("pending_count"),
        )
        .where(and_(*conditions))
        .group_by(time_group)
        .order_by(time_group)
    )

    result = await db.execute(query)
    rows = result.all()

    data = []
    for row in rows:
        total = row.count or 0
        success = row.success_count or 0
        conversion = round((success / total * 100), 2) if total > 0 else 0.0
        data.append(
            TrendPoint(
                timestamp=row.timestamp,
                count=total,
                amount=Decimal(str(row.amount or 0)),
                success_count=success,
                failed_count=row.failed_count or 0,
                pending_count=row.pending_count or 0,
                conversion_rate=conversion,
            )
        )

    return MetricsTrend(
        period={"from": from_date.isoformat(), "to": to_date.isoformat()},
        granularity=granularity,
        data=data,
    )


DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


@router.get("/hourly-distribution", response_model=HourlyDistribution)
async def get_hourly_distribution(
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    source: Optional[str] = Query(None),
    project: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Get hourly distribution for heatmap visualization.
    Returns data grouped by day of week and hour.
    """
    if not to_date:
        to_date = date.today()
    if not from_date:
        from_date = to_date - timedelta(days=6)  # Default: last 7 days

    conditions = [
        Transaction.created_at >= datetime.combine(from_date, datetime.min.time()),
        Transaction.created_at <= datetime.combine(to_date, datetime.max.time()),
    ]
    if source:
        conditions.append(Transaction.source == source)
    if project:
        conditions.append(Transaction.project == project)

    # Extract day of week (0=Monday in PostgreSQL with ISODOW-1) and hour
    day_of_week = func.extract("isodow", Transaction.created_at) - 1
    hour = func.extract("hour", Transaction.created_at)

    query = (
        select(
            day_of_week.label("day_of_week"),
            hour.label("hour"),
            func.count(Transaction.id).label("count"),
            func.count(case((Transaction.status == "success", 1))).label("success_count"),
            func.count(case((Transaction.status == "failed", 1))).label("failed_count"),
        )
        .where(and_(*conditions))
        .group_by(day_of_week, hour)
        .order_by(day_of_week, hour)
    )

    result = await db.execute(query)
    rows = result.all()

    data = []
    for row in rows:
        dow = int(row.day_of_week)
        total = row.count or 0
        success = row.success_count or 0
        data.append(
            HourlyDistributionPoint(
                day_of_week=dow,
                day_name=DAY_NAMES[dow] if dow < 7 else "?",
                hour=int(row.hour),
                count=total,
                success_count=success,
                failed_count=row.failed_count or 0,
                success_rate=round((success / total * 100) if total > 0 else 0, 1),
            )
        )

    return HourlyDistribution(
        period={"from": from_date.isoformat(), "to": to_date.isoformat()},
        data=data,
    )


AMOUNT_BUCKETS = [
    (0, 100, "₹0-100"),
    (100, 500, "₹100-500"),
    (500, 1000, "₹500-1K"),
    (1000, 5000, "₹1K-5K"),
    (5000, 10000, "₹5K-10K"),
    (10000, float("inf"), "₹10K+"),
]


@router.get("/amount-distribution", response_model=AmountDistribution)
async def get_amount_distribution(
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    source: Optional[str] = Query(None),
    project: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Get amount distribution for heatmap by amount buckets and hour.
    """
    if not to_date:
        to_date = date.today()
    if not from_date:
        from_date = to_date - timedelta(days=6)

    conditions = [
        Transaction.created_at >= datetime.combine(from_date, datetime.min.time()),
        Transaction.created_at <= datetime.combine(to_date, datetime.max.time()),
    ]
    if source:
        conditions.append(Transaction.source == source)
    if project:
        conditions.append(Transaction.project == project)

    hour = func.extract("hour", Transaction.created_at)

    # Build CASE expression for amount buckets
    bucket_case = case(
        (Transaction.amount < 100, 0),
        (and_(Transaction.amount >= 100, Transaction.amount < 500), 1),
        (and_(Transaction.amount >= 500, Transaction.amount < 1000), 2),
        (and_(Transaction.amount >= 1000, Transaction.amount < 5000), 3),
        (and_(Transaction.amount >= 5000, Transaction.amount < 10000), 4),
        else_=5,
    )

    query = (
        select(
            bucket_case.label("bucket_index"),
            hour.label("hour"),
            func.count(Transaction.id).label("count"),
            func.coalesce(func.sum(Transaction.amount), 0).label("total_amount"),
        )
        .where(and_(*conditions))
        .group_by(bucket_case, hour)
        .order_by(bucket_case, hour)
    )

    result = await db.execute(query)
    rows = result.all()

    data = []
    for row in rows:
        bucket_idx = int(row.bucket_index)
        bucket_label = AMOUNT_BUCKETS[bucket_idx][2] if bucket_idx < len(AMOUNT_BUCKETS) else "Other"
        data.append(
            AmountBucketPoint(
                bucket=bucket_label,
                bucket_index=bucket_idx,
                hour=int(row.hour),
                count=row.count or 0,
                total_amount=Decimal(str(row.total_amount or 0)),
            )
        )

    return AmountDistribution(
        period={"from": from_date.isoformat(), "to": to_date.isoformat()},
        buckets=[b[2] for b in AMOUNT_BUCKETS],
        data=data,
    )


@router.get("/conversion-by-project", response_model=ConversionByProjectResponse)
async def get_conversion_by_project(
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    source: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Get conversion rates by project with top/bottom 5.
    """
    if not to_date:
        to_date = date.today()
    if not from_date:
        from_date = to_date - timedelta(days=7)

    conditions = [
        Transaction.created_at >= datetime.combine(from_date, datetime.min.time()),
        Transaction.created_at <= datetime.combine(to_date, datetime.max.time()),
    ]
    if source:
        conditions.append(Transaction.source == source)

    query = (
        select(
            Transaction.project,
            func.count(Transaction.id).label("total_count"),
            func.count(case((Transaction.status == "success", 1))).label("success_count"),
            func.count(case((Transaction.status == "failed", 1))).label("failed_count"),
            func.coalesce(func.sum(Transaction.amount), 0).label("total_amount"),
        )
        .where(and_(*conditions))
        .group_by(Transaction.project)
        .having(func.count(Transaction.id) >= 10)  # Min 10 transactions to be meaningful
        .order_by(func.count(Transaction.id).desc())
    )

    result = await db.execute(query)
    rows = result.all()

    projects = []
    for row in rows:
        total = row.total_count or 0
        success = row.success_count or 0
        total_amount = Decimal(str(row.total_amount or 0))
        projects.append(
            ConversionByProject(
                project=row.project or "unknown",
                total_count=total,
                success_count=success,
                failed_count=row.failed_count or 0,
                conversion_rate=round((success / total * 100) if total > 0 else 0, 2),
                avg_ticket=round(total_amount / total, 2) if total > 0 else Decimal(0),
                total_amount=total_amount,
            )
        )

    # Sort by conversion rate for top/bottom
    sorted_by_conversion = sorted(projects, key=lambda p: p.conversion_rate, reverse=True)
    top_5 = sorted_by_conversion[:5]
    bottom_5 = sorted_by_conversion[-5:] if len(sorted_by_conversion) > 5 else sorted_by_conversion

    return ConversionByProjectResponse(
        period={"from": from_date.isoformat(), "to": to_date.isoformat()},
        projects=projects,
        top_5=top_5,
        bottom_5=bottom_5,
    )


@router.get("/by-source", response_model=MetricsBySource)
async def get_metrics_by_source(
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    granularity: str = Query("hour", description="minute | 5min | 15min | hour | day"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get metrics separated by source (vima, payshack) with trends.
    """
    if not to_date:
        to_date = date.today()
    if not from_date:
        if granularity in ("minute", "5min", "15min"):
            from_date = to_date
        elif granularity == "hour":
            from_date = to_date - timedelta(days=1)
        else:
            from_date = to_date - timedelta(days=7)

    sources_data = []

    for source_name in ["vima", "payshack"]:
        conditions = [
            Transaction.created_at >= datetime.combine(from_date, datetime.min.time()),
            Transaction.created_at <= datetime.combine(to_date, datetime.max.time()),
            Transaction.source == source_name,
        ]

        # Time grouping
        if granularity == "minute":
            time_group = func.date_trunc("minute", Transaction.created_at)
        elif granularity == "5min":
            epoch = func.extract("epoch", Transaction.created_at)
            rounded_epoch = func.floor(epoch / 300) * 300
            time_group = func.to_timestamp(rounded_epoch)
        elif granularity == "15min":
            epoch = func.extract("epoch", Transaction.created_at)
            rounded_epoch = func.floor(epoch / 900) * 900
            time_group = func.to_timestamp(rounded_epoch)
        elif granularity == "hour":
            time_group = func.date_trunc("hour", Transaction.created_at)
        else:
            time_group = func.date_trunc("day", Transaction.created_at)

        # Trend query
        trend_query = (
            select(
                time_group.label("timestamp"),
                func.count(Transaction.id).label("count"),
                func.coalesce(func.sum(Transaction.amount), 0).label("amount"),
                func.count(case((Transaction.status == "success", 1))).label("success_count"),
                func.count(case((Transaction.status == "failed", 1))).label("failed_count"),
                func.count(case((Transaction.status == "pending", 1))).label("pending_count"),
            )
            .where(and_(*conditions))
            .group_by(time_group)
            .order_by(time_group)
        )

        result = await db.execute(trend_query)
        rows = result.all()

        data = []
        total_count = 0
        total_amount = Decimal(0)

        for row in rows:
            count = row.count or 0
            success = row.success_count or 0
            conversion = round((success / count * 100), 2) if count > 0 else 0.0
            total_count += count
            total_amount += Decimal(str(row.amount or 0))

            data.append(
                TrendPoint(
                    timestamp=row.timestamp,
                    count=count,
                    amount=Decimal(str(row.amount or 0)),
                    success_count=success,
                    failed_count=row.failed_count or 0,
                    pending_count=row.pending_count or 0,
                    conversion_rate=conversion,
                )
            )

        sources_data.append(
            SourceTrendData(
                source=source_name,
                data=data,
                totals=StatusMetrics(count=total_count, amount=total_amount),
            )
        )

    return MetricsBySource(
        period={"from": from_date.isoformat(), "to": to_date.isoformat()},
        granularity=granularity,
        sources=sources_data,
    )


@router.get("/heatmap", response_model=HeatmapResponse)
async def get_heatmap(
    dimension: str = Query("hour_day", description="hour_day | merchant_hour | merchant_day"),
    metric: str = Query("amount", description="amount | count | conversion"),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    source: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Get heatmap data for visualization.
    
    Dimensions:
    - hour_day: Hour (0-23) x Day of week (Mon-Sun)
    - merchant_hour: Merchant x Hour
    - merchant_day: Merchant x Day of week
    """
    if not to_date:
        to_date = date.today()
    if not from_date:
        from_date = to_date - timedelta(days=6)

    conditions = [
        Transaction.created_at >= datetime.combine(from_date, datetime.min.time()),
        Transaction.created_at <= datetime.combine(to_date, datetime.max.time()),
    ]
    if source:
        conditions.append(Transaction.source == source)

    cells = []
    x_labels = []
    y_labels = []
    min_value = Decimal("999999999")
    max_value = Decimal(0)

    if dimension == "hour_day":
        # Hour x Day of Week
        x_labels = [str(i) for i in range(24)]
        y_labels = DAY_NAMES

        hour = func.extract("hour", Transaction.created_at)
        day_of_week = func.extract("isodow", Transaction.created_at) - 1

        if metric == "conversion":
            query = (
                select(
                    hour.label("hour"),
                    day_of_week.label("dow"),
                    func.count(Transaction.id).label("count"),
                    func.count(case((Transaction.status == "success", 1))).label("success_count"),
                )
                .where(and_(*conditions))
                .group_by(hour, day_of_week)
            )
        else:
            query = (
                select(
                    hour.label("hour"),
                    day_of_week.label("dow"),
                    func.count(Transaction.id).label("count"),
                    func.coalesce(func.sum(Transaction.amount), 0).label("amount"),
                )
                .where(and_(*conditions))
                .group_by(hour, day_of_week)
            )

        result = await db.execute(query)
        for row in result.all():
            h = int(row.hour)
            d = int(row.dow)
            count = row.count or 0

            if metric == "amount":
                value = Decimal(str(row.amount or 0))
            elif metric == "count":
                value = Decimal(count)
            else:  # conversion
                success = row.success_count or 0
                value = Decimal(str(round((success / count * 100), 2) if count > 0 else 0))

            cells.append(HeatmapCell(
                x=str(h),
                y=DAY_NAMES[d] if d < 7 else "?",
                value=value,
                count=count,
            ))
            min_value = min(min_value, value)
            max_value = max(max_value, value)

    elif dimension == "merchant_hour":
        # Merchant x Hour
        x_labels = [str(i) for i in range(24)]

        hour = func.extract("hour", Transaction.created_at)

        query = (
            select(
                Transaction.project,
                hour.label("hour"),
                func.count(Transaction.id).label("count"),
                func.coalesce(func.sum(Transaction.amount), 0).label("amount"),
                func.count(case((Transaction.status == "success", 1))).label("success_count"),
            )
            .where(and_(*conditions))
            .group_by(Transaction.project, hour)
            .order_by(func.sum(Transaction.amount).desc())
        )

        result = await db.execute(query)
        rows = result.all()

        # Get unique projects
        projects = list(dict.fromkeys([r.project or "unknown" for r in rows]))
        y_labels = projects[:20]  # Limit to top 20

        for row in rows:
            proj = row.project or "unknown"
            if proj not in y_labels:
                continue

            h = int(row.hour)
            count = row.count or 0

            if metric == "amount":
                value = Decimal(str(row.amount or 0))
            elif metric == "count":
                value = Decimal(count)
            else:  # conversion
                success = row.success_count or 0
                value = Decimal(str(round((success / count * 100), 2) if count > 0 else 0))

            cells.append(HeatmapCell(
                x=str(h),
                y=proj,
                value=value,
                count=count,
            ))
            min_value = min(min_value, value)
            max_value = max(max_value, value)

    elif dimension == "merchant_day":
        # Merchant x Day of Week
        x_labels = DAY_NAMES

        day_of_week = func.extract("isodow", Transaction.created_at) - 1

        query = (
            select(
                Transaction.project,
                day_of_week.label("dow"),
                func.count(Transaction.id).label("count"),
                func.coalesce(func.sum(Transaction.amount), 0).label("amount"),
                func.count(case((Transaction.status == "success", 1))).label("success_count"),
            )
            .where(and_(*conditions))
            .group_by(Transaction.project, day_of_week)
            .order_by(func.sum(Transaction.amount).desc())
        )

        result = await db.execute(query)
        rows = result.all()

        # Get unique projects
        projects = list(dict.fromkeys([r.project or "unknown" for r in rows]))
        y_labels = projects[:20]  # Limit to top 20

        for row in rows:
            proj = row.project or "unknown"
            if proj not in y_labels:
                continue

            d = int(row.dow)
            count = row.count or 0

            if metric == "amount":
                value = Decimal(str(row.amount or 0))
            elif metric == "count":
                value = Decimal(count)
            else:  # conversion
                success = row.success_count or 0
                value = Decimal(str(round((success / count * 100), 2) if count > 0 else 0))

            cells.append(HeatmapCell(
                x=DAY_NAMES[d] if d < 7 else "?",
                y=proj,
                value=value,
                count=count,
            ))
            min_value = min(min_value, value)
            max_value = max(max_value, value)

    # Handle case when no data
    if min_value == Decimal("999999999"):
        min_value = Decimal(0)

    return HeatmapResponse(
        dimension=dimension,
        metric=metric,
        x_labels=x_labels,
        y_labels=y_labels,
        cells=cells,
        min_value=min_value,
        max_value=max_value,
    )


# Country name mapping
COUNTRY_NAMES = {
    "IN": "India",
    "US": "United States",
    "GB": "United Kingdom",
    "AE": "UAE",
    "SG": "Singapore",
    "BD": "Bangladesh",
    "NP": "Nepal",
    "PK": "Pakistan",
    "LK": "Sri Lanka",
}


@router.get("/comparison", response_model=PeriodComparisonResponse)
async def get_period_comparison(
    comparison_type: str = Query("day", description="day | week | month"),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    source: Optional[str] = Query(None),
    project: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Compare current period with previous period.
    
    comparison_type:
    - day: Today vs Yesterday
    - week: This week vs Last week
    - month: This month vs Last month
    """
    # Calculate periods
    if to_date is None:
        to_date = date.today()

    if comparison_type == "day":
        current_from = to_date
        current_to = to_date
        previous_from = to_date - timedelta(days=1)
        previous_to = previous_from
    elif comparison_type == "week":
        # Current week (Mon-today)
        days_since_monday = to_date.weekday()
        current_from = to_date - timedelta(days=days_since_monday)
        current_to = to_date
        # Previous week
        previous_to = current_from - timedelta(days=1)
        previous_from = previous_to - timedelta(days=6)
    else:  # month
        current_from = to_date.replace(day=1)
        current_to = to_date
        # Previous month
        previous_to = current_from - timedelta(days=1)
        previous_from = previous_to.replace(day=1)

    async def get_metrics_for_period(period_from: date, period_to: date) -> dict:
        conditions = [
            Transaction.created_at >= datetime.combine(period_from, datetime.min.time()),
            Transaction.created_at <= datetime.combine(period_to, datetime.max.time()),
        ]
        if source:
            conditions.append(Transaction.source == source)
        if project:
            conditions.append(Transaction.project == project)

        query = select(
            func.count(Transaction.id).label("total_count"),
            func.coalesce(func.sum(Transaction.amount), 0).label("total_amount"),
            func.count(case((Transaction.status == "success", 1))).label("success_count"),
            func.coalesce(
                func.sum(case((Transaction.status == "success", Transaction.amount))), 0
            ).label("success_amount"),
            func.count(case((Transaction.status == "failed", 1))).label("failed_count"),
        ).where(and_(*conditions))

        result = await db.execute(query)
        row = result.one()

        total_count = row.total_count or 0
        total_amount = Decimal(str(row.total_amount or 0))
        success_count = row.success_count or 0
        success_amount = Decimal(str(row.success_amount or 0))

        return {
            "total_count": total_count,
            "total_amount": total_amount,
            "success_count": success_count,
            "success_amount": success_amount,
            "failed_count": row.failed_count or 0,
            "conversion_rate": round((success_count / total_count * 100), 2) if total_count > 0 else 0,
            "avg_ticket": round(total_amount / total_count, 2) if total_count > 0 else Decimal(0),
        }

    current_metrics = await get_metrics_for_period(current_from, current_to)
    previous_metrics = await get_metrics_for_period(previous_from, previous_to)

    # Calculate changes
    def safe_percent_change(current, previous):
        if previous == 0:
            return 100.0 if current > 0 else 0.0
        return round(((current - previous) / previous) * 100, 2)

    count_change = current_metrics["total_count"] - previous_metrics["total_count"]
    amount_change = current_metrics["total_amount"] - previous_metrics["total_amount"]
    conversion_change = current_metrics["conversion_rate"] - previous_metrics["conversion_rate"]
    avg_ticket_change = current_metrics["avg_ticket"] - previous_metrics["avg_ticket"]

    return PeriodComparisonResponse(
        current=PeriodMetrics(
            period_name="current",
            from_date=current_from.isoformat(),
            to_date=current_to.isoformat(),
            total_count=current_metrics["total_count"],
            total_amount=current_metrics["total_amount"],
            success_count=current_metrics["success_count"],
            success_amount=current_metrics["success_amount"],
            failed_count=current_metrics["failed_count"],
            conversion_rate=current_metrics["conversion_rate"],
            avg_ticket=current_metrics["avg_ticket"],
        ),
        previous=PeriodMetrics(
            period_name="previous",
            from_date=previous_from.isoformat(),
            to_date=previous_to.isoformat(),
            total_count=previous_metrics["total_count"],
            total_amount=previous_metrics["total_amount"],
            success_count=previous_metrics["success_count"],
            success_amount=previous_metrics["success_amount"],
            failed_count=previous_metrics["failed_count"],
            conversion_rate=previous_metrics["conversion_rate"],
            avg_ticket=previous_metrics["avg_ticket"],
        ),
        comparison=MetricComparison(
            count_change=count_change,
            count_change_percent=safe_percent_change(
                current_metrics["total_count"], previous_metrics["total_count"]
            ),
            amount_change=amount_change,
            amount_change_percent=safe_percent_change(
                float(current_metrics["total_amount"]), float(previous_metrics["total_amount"])
            ),
            conversion_change=round(conversion_change, 2),
            avg_ticket_change=avg_ticket_change,
            avg_ticket_change_percent=safe_percent_change(
                float(current_metrics["avg_ticket"]), float(previous_metrics["avg_ticket"])
            ),
        ),
    )


@router.get("/by-country", response_model=MetricsByCountry)
async def get_metrics_by_country(
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    source: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Get metrics grouped by country."""
    if not to_date:
        to_date = date.today()
    if not from_date:
        from_date = to_date - timedelta(days=7)

    conditions = [
        Transaction.created_at >= datetime.combine(from_date, datetime.min.time()),
        Transaction.created_at <= datetime.combine(to_date, datetime.max.time()),
    ]
    if source:
        conditions.append(Transaction.source == source)

    # Get totals first
    totals_query = select(
        func.count(Transaction.id).label("total_count"),
        func.coalesce(func.sum(Transaction.amount), 0).label("total_amount"),
    ).where(and_(*conditions))

    totals_result = await db.execute(totals_query)
    totals_row = totals_result.one()
    grand_total_count = totals_row.total_count or 0
    grand_total_amount = Decimal(str(totals_row.total_amount or 0))

    # Get metrics by country
    query = (
        select(
            Transaction.country,
            func.count(Transaction.id).label("total_count"),
            func.coalesce(func.sum(Transaction.amount), 0).label("total_amount"),
            func.count(case((Transaction.status == "success", 1))).label("success_count"),
            func.count(case((Transaction.status == "failed", 1))).label("failed_count"),
        )
        .where(and_(*conditions))
        .group_by(Transaction.country)
        .order_by(func.sum(Transaction.amount).desc())
    )

    result = await db.execute(query)
    rows = result.all()

    countries = []
    for row in rows:
        country_code = row.country or "XX"
        total = row.total_count or 0
        success = row.success_count or 0
        total_amount = Decimal(str(row.total_amount or 0))

        percentage = (
            round(float(total_amount) / float(grand_total_amount) * 100, 2)
            if grand_total_amount > 0
            else 0
        )

        countries.append(
            CountryMetrics(
                country=country_code,
                country_name=COUNTRY_NAMES.get(country_code, country_code),
                total_count=total,
                total_amount=total_amount,
                success_count=success,
                failed_count=row.failed_count or 0,
                conversion_rate=round((success / total * 100), 2) if total > 0 else 0,
                avg_ticket=round(total_amount / total, 2) if total > 0 else Decimal(0),
                percentage_of_total=percentage,
            )
        )

    return MetricsByCountry(
        period={"from": from_date.isoformat(), "to": to_date.isoformat()},
        countries=countries,
        total_count=grand_total_count,
        total_amount=grand_total_amount,
    )


@router.get("/by-merchant", response_model=MerchantListResponse)
async def get_metrics_by_merchant(
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    source: Optional[str] = Query(None),
    search: Optional[str] = Query(None, description="Search by project name"),
    sort_by: str = Query("total_amount", description="total_amount | total_count | conversion_rate"),
    order: str = Query("desc", description="asc | desc"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed metrics for merchants/projects with pagination."""
    if not to_date:
        to_date = date.today()
    if not from_date:
        from_date = to_date - timedelta(days=7)

    conditions = [
        Transaction.created_at >= datetime.combine(from_date, datetime.min.time()),
        Transaction.created_at <= datetime.combine(to_date, datetime.max.time()),
    ]
    if source:
        conditions.append(Transaction.source == source)
    if search:
        conditions.append(Transaction.project.ilike(f"%{search}%"))

    # Count total merchants
    count_query = (
        select(func.count(func.distinct(Transaction.project)))
        .where(and_(*conditions))
    )
    count_result = await db.execute(count_query)
    total_merchants = count_result.scalar() or 0

    # Build order by clause
    sort_field_map = {
        "total_amount": func.sum(Transaction.amount),
        "total_count": func.count(Transaction.id),
        "conversion_rate": func.count(case((Transaction.status == "success", 1))) * 100.0 / func.count(Transaction.id),
    }
    order_by_field = sort_field_map.get(sort_by, func.sum(Transaction.amount))
    if order == "asc":
        order_by_clause = order_by_field.asc()
    else:
        order_by_clause = order_by_field.desc()

    # Main query with pagination
    query = (
        select(
            Transaction.project,
            func.count(Transaction.id).label("total_count"),
            func.coalesce(func.sum(Transaction.amount), 0).label("total_amount"),
            func.count(case((Transaction.status == "success", 1))).label("success_count"),
            func.coalesce(
                func.sum(case((Transaction.status == "success", Transaction.amount))), 0
            ).label("success_amount"),
            func.count(case((Transaction.status == "failed", 1))).label("failed_count"),
            func.coalesce(
                func.sum(case((Transaction.status == "failed", Transaction.amount))), 0
            ).label("failed_amount"),
            func.count(case((Transaction.status == "pending", 1))).label("pending_count"),
            func.min(Transaction.created_at).label("first_txn_at"),
            func.max(Transaction.created_at).label("last_txn_at"),
        )
        .where(and_(*conditions))
        .group_by(Transaction.project)
        .order_by(order_by_clause)
        .offset((page - 1) * limit)
        .limit(limit)
    )

    result = await db.execute(query)
    rows = result.all()

    merchants = []
    for row in rows:
        total = row.total_count or 0
        success = row.success_count or 0
        total_amount = Decimal(str(row.total_amount or 0))

        merchants.append(
            MerchantMetrics(
                merchant_id=row.project or "unknown",
                project=row.project or "unknown",
                total_count=total,
                total_amount=total_amount,
                success_count=success,
                success_amount=Decimal(str(row.success_amount or 0)),
                failed_count=row.failed_count or 0,
                failed_amount=Decimal(str(row.failed_amount or 0)),
                pending_count=row.pending_count or 0,
                conversion_rate=round((success / total * 100), 2) if total > 0 else 0,
                avg_ticket=round(total_amount / total, 2) if total > 0 else Decimal(0),
                first_txn_at=row.first_txn_at,
                last_txn_at=row.last_txn_at,
            )
        )

    total_pages = (total_merchants + limit - 1) // limit

    return MerchantListResponse(
        period={"from": from_date.isoformat(), "to": to_date.isoformat()},
        merchants=merchants,
        total=total_merchants,
        page=page,
        limit=limit,
        pages=total_pages,
    )


@router.get("/rpm", response_model=RPMResponse)
async def get_rpm_metrics(
    minutes: int = Query(60, ge=5, le=1440, description="Number of minutes to analyze"),
    source: Optional[str] = Query(None),
    project: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Get RPM (Requests/Transactions Per Minute) metrics.
    
    Shows transaction rate over time for monitoring and capacity planning.
    """
    now = datetime.now()
    from_time = now - timedelta(minutes=minutes)

    conditions = [
        Transaction.created_at >= from_time,
        Transaction.created_at <= now,
    ]
    if source:
        conditions.append(Transaction.source == source)
    if project:
        conditions.append(Transaction.project == project)

    # Group by minute
    minute_group = func.date_trunc("minute", Transaction.created_at)

    query = (
        select(
            minute_group.label("timestamp"),
            func.count(Transaction.id).label("count"),
            func.count(case((Transaction.status == "success", 1))).label("success_count"),
            func.count(case((Transaction.status == "failed", 1))).label("failed_count"),
        )
        .where(and_(*conditions))
        .group_by(minute_group)
        .order_by(minute_group)
    )

    result = await db.execute(query)
    rows = result.all()

    data = []
    rpm_values = []
    total_transactions = 0

    for row in rows:
        rpm = float(row.count or 0)  # Transactions in this minute
        success_rpm = float(row.success_count or 0)
        failed_rpm = float(row.failed_count or 0)
        total_transactions += row.count or 0

        rpm_values.append(rpm)
        data.append(
            RPMPoint(
                timestamp=row.timestamp,
                rpm=rpm,
                success_rpm=success_rpm,
                failed_rpm=failed_rpm,
                avg_response_time_ms=None,  # Would need timing data
            )
        )

    # Calculate aggregates
    current_rpm = rpm_values[-1] if rpm_values else 0.0
    avg_rpm = sum(rpm_values) / len(rpm_values) if rpm_values else 0.0
    max_rpm = max(rpm_values) if rpm_values else 0.0
    min_rpm = min(rpm_values) if rpm_values else 0.0

    return RPMResponse(
        period={
            "from": from_time.isoformat(),
            "to": now.isoformat(),
        },
        current_rpm=round(current_rpm, 2),
        avg_rpm=round(avg_rpm, 2),
        max_rpm=round(max_rpm, 2),
        min_rpm=round(min_rpm, 2),
        total_transactions=total_transactions,
        data=data,
    )


@router.get("/live", response_model=LiveMetrics)
async def get_live_metrics(
    source: Optional[str] = Query(None),
    project: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Get real-time live metrics (last 5 minutes).
    
    Designed for live dashboard updates.
    """
    now = datetime.now()
    last_minute = now - timedelta(minutes=1)
    last_5min = now - timedelta(minutes=5)

    # Last minute metrics (for current RPM)
    rpm_conditions = [
        Transaction.created_at >= last_minute,
        Transaction.created_at <= now,
    ]
    if source:
        rpm_conditions.append(Transaction.source == source)
    if project:
        rpm_conditions.append(Transaction.project == project)

    rpm_query = select(
        func.count(Transaction.id).label("count"),
        func.count(case((Transaction.status == "success", 1))).label("success_count"),
    ).where(and_(*rpm_conditions))

    rpm_result = await db.execute(rpm_query)
    rpm_row = rpm_result.one()
    current_rpm = float(rpm_row.count or 0)

    # Last 5 minutes metrics
    conditions_5min = [
        Transaction.created_at >= last_5min,
        Transaction.created_at <= now,
    ]
    if source:
        conditions_5min.append(Transaction.source == source)
    if project:
        conditions_5min.append(Transaction.project == project)

    query_5min = select(
        func.count(Transaction.id).label("count"),
        func.coalesce(func.sum(Transaction.amount), 0).label("amount"),
        func.count(case((Transaction.status == "success", 1))).label("success_count"),
        func.count(case((Transaction.status == "pending", 1))).label("pending_count"),
        func.coalesce(
            func.avg(case((Transaction.status == "success", Transaction.amount))), 0
        ).label("avg_ticket"),
    ).where(and_(*conditions_5min))

    result_5min = await db.execute(query_5min)
    row_5min = result_5min.one()

    count_5min = row_5min.count or 0
    success_5min = row_5min.success_count or 0
    success_rate_5min = round((success_5min / count_5min * 100), 2) if count_5min > 0 else 0.0

    return LiveMetrics(
        timestamp=now,
        current_rpm=current_rpm,
        success_rate=success_rate_5min,
        avg_ticket=Decimal(str(row_5min.avg_ticket or 0)),
        pending_count=row_5min.pending_count or 0,
        last_5min_count=count_5min,
        last_5min_amount=Decimal(str(row_5min.amount or 0)),
        last_5min_success_rate=success_rate_5min,
    )


@router.get("/horizontal-bars/{metric_type}", response_model=HorizontalBarResponse)
async def get_horizontal_bar_data(
    metric_type: str,  # "volume-by-project" | "count-by-project" | "volume-by-status" | "conversion-by-project"
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    source: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """
    Get data formatted for horizontal bar charts.
    
    Metric types:
    - volume-by-project: Transaction volume by project
    - count-by-project: Transaction count by project
    - volume-by-status: Volume breakdown by status
    - conversion-by-project: Conversion rate by project
    """
    if not to_date:
        to_date = date.today()
    if not from_date:
        from_date = to_date - timedelta(days=7)

    conditions = [
        Transaction.created_at >= datetime.combine(from_date, datetime.min.time()),
        Transaction.created_at <= datetime.combine(to_date, datetime.max.time()),
    ]
    if source:
        conditions.append(Transaction.source == source)

    items = []
    total = Decimal(0)
    metric_name = metric_type

    if metric_type in ("volume-by-project", "count-by-project", "conversion-by-project"):
        # Group by project
        if metric_type == "conversion-by-project":
            # Order by conversion rate
            order_field = func.count(case((Transaction.status == "success", 1))) * 100.0 / func.count(Transaction.id)
        elif metric_type == "volume-by-project":
            order_field = func.sum(Transaction.amount)
        else:
            order_field = func.count(Transaction.id)

        query = (
            select(
                Transaction.project,
                func.count(Transaction.id).label("count"),
                func.coalesce(func.sum(Transaction.amount), 0).label("amount"),
                func.count(case((Transaction.status == "success", 1))).label("success_count"),
            )
            .where(and_(*conditions))
            .group_by(Transaction.project)
            .order_by(order_field.desc())
            .limit(limit)
        )

        result = await db.execute(query)
        rows = result.all()

        # Calculate total for percentage
        if metric_type == "volume-by-project":
            total = sum(Decimal(str(r.amount or 0)) for r in rows)
        else:
            total = Decimal(sum(r.count or 0 for r in rows))

        for row in rows:
            project_name = row.project or "unknown"
            count = row.count or 0
            amount = Decimal(str(row.amount or 0))
            success = row.success_count or 0

            if metric_type == "volume-by-project":
                value = amount
                percentage = float(amount / total * 100) if total > 0 else 0
            elif metric_type == "count-by-project":
                value = Decimal(count)
                percentage = float(count / float(total) * 100) if total > 0 else 0
            else:  # conversion-by-project
                conversion = round((success / count * 100), 2) if count > 0 else 0
                value = Decimal(str(conversion))
                percentage = conversion  # For conversion, percentage IS the value

            items.append(
                HorizontalBarItem(
                    label=project_name,
                    value=value,
                    count=count,
                    percentage=round(percentage, 2),
                )
            )

    elif metric_type == "volume-by-status":
        # Group by status
        query = (
            select(
                Transaction.status,
                func.count(Transaction.id).label("count"),
                func.coalesce(func.sum(Transaction.amount), 0).label("amount"),
            )
            .where(and_(*conditions))
            .group_by(Transaction.status)
            .order_by(func.sum(Transaction.amount).desc())
        )

        result = await db.execute(query)
        rows = result.all()

        total = sum(Decimal(str(r.amount or 0)) for r in rows)

        status_labels = {
            "success": "Success",
            "failed": "Failed",
            "pending": "Pending",
            "processing": "Processing",
            "refunded": "Refunded",
        }

        for row in rows:
            status = row.status or "unknown"
            count = row.count or 0
            amount = Decimal(str(row.amount or 0))
            percentage = float(amount / total * 100) if total > 0 else 0

            items.append(
                HorizontalBarItem(
                    label=status_labels.get(status, status.capitalize()),
                    value=amount,
                    count=count,
                    percentage=round(percentage, 2),
                )
            )

    return HorizontalBarResponse(
        period={"from": from_date.isoformat(), "to": to_date.isoformat()},
        metric=metric_name,
        items=items,
        total=total,
    )
