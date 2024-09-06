--
-- PostgreSQL database dump
--

-- Dumped from database version 15.8 (Debian 15.8-0+deb12u1)
-- Dumped by pg_dump version 15.8 (Debian 15.8-0+deb12u1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: boats; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.boats (
    uid integer NOT NULL,
    bibnumber1 integer,
    bibnumber2 integer,
    boatnumber integer NOT NULL
);


ALTER TABLE public.boats OWNER TO postgres;

--
-- Name: boats_boatnumber_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.boats_boatnumber_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.boats_boatnumber_seq OWNER TO postgres;

--
-- Name: boats_boatnumber_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.boats_boatnumber_seq OWNED BY public.boats.boatnumber;


--
-- Name: boats_uid_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.boats_uid_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.boats_uid_seq OWNER TO postgres;

--
-- Name: boats_uid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.boats_uid_seq OWNED BY public.boats.uid;


--
-- Name: demodata; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.demodata (
    uid integer NOT NULL,
    fname character varying(255),
    lname character varying(255),
    gender character varying(255),
    age character varying(255),
    council character varying(255),
    district character varying(255),
    unittype character varying(255),
    unitnumber integer,
    race character varying(255),
    boat character varying(255),
    bibnumber integer
);


ALTER TABLE public.demodata OWNER TO postgres;

--
-- Name: demodata_uid_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.demodata_uid_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.demodata_uid_seq OWNER TO postgres;

--
-- Name: demodata_uid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.demodata_uid_seq OWNED BY public.demodata.uid;


--
-- Name: linker; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.linker (
    uid integer NOT NULL,
    bibnumber integer,
    rfidtag character varying(255),
    tag_type character varying(255),
    tag_id character varying(255),
    tag_position character varying(255)
);


ALTER TABLE public.linker OWNER TO postgres;

--
-- Name: linker_uid_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.linker_uid_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.linker_uid_seq OWNER TO postgres;

--
-- Name: linker_uid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.linker_uid_seq OWNED BY public.linker.uid;


--
-- Name: timeresults; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.timeresults (
    id integer NOT NULL,
    tag_type character varying(255),
    tag_id character varying(255),
    tag_position character varying(255),
    "timestamp" double precision,
    timestamp_h character varying(255)
);


ALTER TABLE public.timeresults OWNER TO postgres;

--
-- Name: timeresults_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.timeresults_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.timeresults_id_seq OWNER TO postgres;

--
-- Name: timeresults_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.timeresults_id_seq OWNED BY public.timeresults.id;


--
-- Name: boats uid; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.boats ALTER COLUMN uid SET DEFAULT nextval('public.boats_uid_seq'::regclass);


--
-- Name: boats boatnumber; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.boats ALTER COLUMN boatnumber SET DEFAULT nextval('public.boats_boatnumber_seq'::regclass);


--
-- Name: demodata uid; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.demodata ALTER COLUMN uid SET DEFAULT nextval('public.demodata_uid_seq'::regclass);


--
-- Name: linker uid; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.linker ALTER COLUMN uid SET DEFAULT nextval('public.linker_uid_seq'::regclass);


--
-- Name: timeresults id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.timeresults ALTER COLUMN id SET DEFAULT nextval('public.timeresults_id_seq'::regclass);


--
-- Name: boats boats_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.boats
    ADD CONSTRAINT boats_pkey PRIMARY KEY (uid);


--
-- Name: demodata demodata_bibnumber_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.demodata
    ADD CONSTRAINT demodata_bibnumber_key UNIQUE (bibnumber);


--
-- Name: demodata demodata_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.demodata
    ADD CONSTRAINT demodata_pkey PRIMARY KEY (uid);


--
-- Name: linker linker_bibnumber_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.linker
    ADD CONSTRAINT linker_bibnumber_key UNIQUE (bibnumber);


--
-- Name: linker linker_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.linker
    ADD CONSTRAINT linker_pkey PRIMARY KEY (uid);


--
-- Name: linker linker_rfidtag_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.linker
    ADD CONSTRAINT linker_rfidtag_key UNIQUE (rfidtag);


--
-- Name: timeresults timeresults_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.timeresults
    ADD CONSTRAINT timeresults_pkey PRIMARY KEY (id);


--
-- Name: boats unique_bibnumber_pair; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.boats
    ADD CONSTRAINT unique_bibnumber_pair UNIQUE (bibnumber1, bibnumber2);


--
-- PostgreSQL database dump complete
--

