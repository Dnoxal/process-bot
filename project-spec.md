# CS Careers Process Tracker Bot

## Overview

The **CS Careers Process Tracker Bot** is a Discord bot designed for the
**CS Careers** server to help members log and track their recruiting
progress with companies. Users can submit structured updates through
commands such as:

    !process amazon oa
    !process google rejected phone
    !process stripe offer

The bot stores these updates in a backend database and exposes the data
to a frontend dashboard that visualizes:

-   company-specific interview trends
-   stage-by-stage recruiting outcomes
-   aggregate acceptance/rejection trends
-   recruiting funnel metrics
-   seasonal recruiting activity

The goal is to turn informal recruiting updates in Discord into
structured data that powers useful career insights for the community.

------------------------------------------------------------------------

# Goals

## Primary Goals

-   Allow users to easily log recruiting updates from Discord
-   Standardize recruiting stage data across companies
-   Store updates in a structured database
-   Provide backend APIs for a frontend analytics dashboard
-   Help server members understand recruiting trends in tech

## Secondary Goals

-   Reduce manual spreadsheet tracking
-   Encourage consistent community participation
-   Surface trends like which companies are sending OAs or offers
-   Build historical recruiting datasets over time

------------------------------------------------------------------------

# Core Use Case

A user in a process-tracking channel wants to record recruiting
progress.

Example commands:

    !process amazon oa
    !process meta phone
    !process google final
    !process stripe offer
    !process robinhood rejected final

The bot should:

1.  Parse the command
2.  Identify the company
3.  Identify the recruiting stage and outcome
4.  Associate the event with the user and timestamp
5.  Save it to the database
6.  Confirm the entry in Discord

------------------------------------------------------------------------

# Scope

## In Scope

-   Discord bot command handling
-   Parsing structured process commands
-   Database storage
-   Backend analytics API
-   Admin correction tools
-   Dashboard-ready analytics summaries


------------------------------------------------------------------------

# User Stories

## Member Users

-   Log recruiting updates with a quick command
-   View their own process history
-   Contribute anonymously to community recruiting statistics

## Admins

-   Configure allowed bot channels
-   Manage standardized company names
-   Correct malformed entries
-   Access aggregate recruiting statistics

## Dashboard Users

-   View company recruiting funnels
-   Filter statistics by time
-   Observe recruiting trends across companies

------------------------------------------------------------------------

# Functional Requirements

## Discord Commands

Primary command:

    !process <company> <stage>
    !process <company> <outcome> <stage>

Examples:

    !process amazon oa
    !process google rejected phone
    !process stripe offer

### Additional Commands

    !myprocesses
    !editprocess <id>
    !deleteprocess <id>
    !companies
    !stats <company>
    !help process

------------------------------------------------------------------------

# Supported Recruiting Stages

Standard stages:

-   applied
-   oa
-   recruiter
-   phone
-   technical
-   behavioral
-   onsite
-   final

Possible outcomes:

-   advanced
-   rejected
-   offered
-   withdrawn
-   accepted

Aliases should map user input to standardized versions.

------------------------------------------------------------------------

# Data Capture

Each process log should store:

-   Discord user ID
-   Username snapshot
-   Company
-   Normalized company ID
-   Recruiting stage
-   Outcome
-   Timestamp
-   Discord message ID
-   Channel ID
-   Recruiting season if inferred
-   Optional notes

------------------------------------------------------------------------

# Architecture

High-level system architecture:

1.  Discord Bot Service
2.  Backend API
3.  Database
4.  Frontend Dashboard

### Discord Bot

Responsibilities:

-   listen for commands
-   parse inputs
-   normalize data
-   store process events

### Backend API

Responsibilities:

-   provide analytics endpoints
-   support dashboard queries
-   handle admin data corrections

### Database

Recommended database: **PostgreSQL**

Stores:

-   users
-   companies
-   company aliases
-   process events
-   audit logs

### Frontend Dashboard

Recommended stack:

-   React
-   Next.js

Displays recruiting statistics and trends.

------------------------------------------------------------------------

# Tech Stack

Bot: - Python + discord.py 

Backend: - FastAPI (Python) 

Database: - PostgreSQL/TBD

Frontend: - React / Next.js

Hosting: - Railway - Render - Fly.io - AWS

------------------------------------------------------------------------

# Data Model

## Users

  Field             Description
  ----------------- -------------------
  id                internal ID
  discord_user_id   Discord ID
  username          snapshot username
  created_at        timestamp

## Companies

  Field   Description
  ------- -----------------
  id      internal ID
  name    company name
  slug    normalized slug

## Company Aliases

  Field        Description
  ------------ -------------
  id           alias ID
  company_id   reference
  alias        alias text

## Process Events

  Field        Description
  ------------ ------------------
  id           event ID
  user_id      user
  company_id   company
  stage        stage
  outcome      optional outcome
  timestamp    event time
  message_id   discord message

------------------------------------------------------------------------

# Example Bot Response

User command:

    !process amazon oa

Bot response:

    Logged: Amazon - OA

User command:

    !process google rejected phone

Bot response:

    Logged: Google - Phone - Rejected

------------------------------------------------------------------------

# API Endpoints

## Public

    GET /api/stats/global
    GET /api/stats/company/:slug
    GET /api/stats/trends
    GET /api/companies

## User

    GET /api/me/processes
    POST /api/process-events
    PATCH /api/process-events/:id
    DELETE /api/process-events/:id

## Admin

    POST /api/companies
    POST /api/company-aliases
    GET /api/admin/process-events
    PATCH /api/admin/process-events/:id

------------------------------------------------------------------------

# Example Analytics

### Company Metrics

-   number of candidates
-   number of OAs
-   number of phone interviews
-   number of onsites
-   number of offers
-   rejection rate by stage

### Global Metrics

-   most active companies
-   recruiting stage distribution
-   trends by week or month
-   offer rates by company

------------------------------------------------------------------------

# Privacy Considerations

-   Public dashboards should only show aggregated data
-   Avoid exposing individual recruiting outcomes
-   Allow users to delete their data
-   Provide admin controls for removing sensitive entries

------------------------------------------------------------------------

# MVP Definition

Minimum viable product should include:

-   `!process` command
-   company normalization
-   stage normalization
-   event database storage
-   bot confirmation messages
-   simple analytics API
-   basic frontend dashboard

------------------------------------------------------------------------

# Future Enhancements

Possible later improvements:

-   Discord slash commands
-   autocomplete for companies
-   seasonal tagging (Summer 2027 etc.)
-   CSV export
-   advanced recruiting funnel analytics
-   notification systems for recruiting trends

------------------------------------------------------------------------

# Success Criteria

The system is successful if:

-   users can log updates quickly
-   commands are parsed correctly
-   analytics queries work reliably
-   dashboard insights are useful to the community
