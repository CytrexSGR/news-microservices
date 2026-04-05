--
-- PostgreSQL database dump
--

\restrict 9K4dMansff3vWUHCE6IGAOv0WJs34h3g6gxfra7J7jdsxBlVgciIKtgK8lbLSU0

-- Dumped from database version 15.15 (Debian 15.15-1.pgdg12+1)
-- Dumped by pg_dump version 15.15 (Debian 15.15-1.pgdg12+1)

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
-- Name: entity_aliases; Type: TABLE; Schema: public; Owner: news_user
--

CREATE TABLE public.entity_aliases (
    id integer NOT NULL,
    canonical_id integer NOT NULL,
    alias character varying(255) NOT NULL,
    created_at timestamp without time zone NOT NULL
);


ALTER TABLE public.entity_aliases OWNER TO news_user;

--
-- Name: entity_aliases_id_seq; Type: SEQUENCE; Schema: public; Owner: news_user
--

CREATE SEQUENCE public.entity_aliases_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.entity_aliases_id_seq OWNER TO news_user;

--
-- Name: entity_aliases_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: news_user
--

ALTER SEQUENCE public.entity_aliases_id_seq OWNED BY public.entity_aliases.id;


--
-- Name: feed_items; Type: TABLE; Schema: public; Owner: news_user
--

CREATE TABLE public.feed_items (
    id uuid NOT NULL,
    feed_id uuid,
    title character varying(500) NOT NULL,
    link text NOT NULL,
    description text,
    content text,
    author character varying(200),
    guid character varying(500),
    published_at timestamp with time zone,
    content_hash character varying(64) NOT NULL,
    scraped_at timestamp with time zone,
    scrape_status character varying(50),
    scrape_word_count integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    scraped_metadata jsonb,
    source_type character varying(50) DEFAULT 'rss'::character varying NOT NULL,
    source_metadata jsonb DEFAULT '{}'::jsonb,
    parent_article_id uuid,
    source_id uuid,
    CONSTRAINT chk_feed_id_required_for_rss CHECK (((((source_type)::text = 'rss'::text) AND (feed_id IS NOT NULL)) OR ((source_type)::text <> 'rss'::text)))
);


ALTER TABLE public.feed_items OWNER TO news_user;

--
-- Name: TABLE feed_items; Type: COMMENT; Schema: public; Owner: news_user
--

COMMENT ON TABLE public.feed_items IS 'Articles from various sources: RSS feeds, Perplexity research, scraping, etc.';


--
-- Name: COLUMN feed_items.source_type; Type: COMMENT; Schema: public; Owner: news_user
--

COMMENT ON COLUMN public.feed_items.source_type IS 'Source type: rss, perplexity_research, scraping, manual, api_*';


--
-- Name: COLUMN feed_items.source_metadata; Type: COMMENT; Schema: public; Owner: news_user
--

COMMENT ON COLUMN public.feed_items.source_metadata IS 'Source-specific metadata (e.g., model, cost, query for perplexity)';


--
-- Name: COLUMN feed_items.parent_article_id; Type: COMMENT; Schema: public; Owner: news_user
--

COMMENT ON COLUMN public.feed_items.parent_article_id IS 'References original article for research/derived content';


--
-- Name: entity_aliases id; Type: DEFAULT; Schema: public; Owner: news_user
--

ALTER TABLE ONLY public.entity_aliases ALTER COLUMN id SET DEFAULT nextval('public.entity_aliases_id_seq'::regclass);


--
-- Name: entity_aliases entity_aliases_pkey; Type: CONSTRAINT; Schema: public; Owner: news_user
--

ALTER TABLE ONLY public.entity_aliases
    ADD CONSTRAINT entity_aliases_pkey PRIMARY KEY (id);


--
-- Name: feed_items feed_items_content_hash_key; Type: CONSTRAINT; Schema: public; Owner: news_user
--

ALTER TABLE ONLY public.feed_items
    ADD CONSTRAINT feed_items_content_hash_key UNIQUE (content_hash);


--
-- Name: feed_items feed_items_pkey; Type: CONSTRAINT; Schema: public; Owner: news_user
--

ALTER TABLE ONLY public.feed_items
    ADD CONSTRAINT feed_items_pkey PRIMARY KEY (id);


--
-- Name: idx_feed_items_parent_article_id; Type: INDEX; Schema: public; Owner: news_user
--

CREATE INDEX idx_feed_items_parent_article_id ON public.feed_items USING btree (parent_article_id);


--
-- Name: idx_feed_items_parent_source; Type: INDEX; Schema: public; Owner: news_user
--

CREATE INDEX idx_feed_items_parent_source ON public.feed_items USING btree (parent_article_id, source_type) WHERE (parent_article_id IS NOT NULL);


--
-- Name: idx_feed_items_scraped_metadata; Type: INDEX; Schema: public; Owner: news_user
--

CREATE INDEX idx_feed_items_scraped_metadata ON public.feed_items USING gin (scraped_metadata);


--
-- Name: idx_feed_items_source_type; Type: INDEX; Schema: public; Owner: news_user
--

CREATE INDEX idx_feed_items_source_type ON public.feed_items USING btree (source_type);


--
-- Name: ix_entity_aliases_alias; Type: INDEX; Schema: public; Owner: news_user
--

CREATE UNIQUE INDEX ix_entity_aliases_alias ON public.entity_aliases USING btree (alias);


--
-- Name: ix_entity_aliases_canonical_id; Type: INDEX; Schema: public; Owner: news_user
--

CREATE INDEX ix_entity_aliases_canonical_id ON public.entity_aliases USING btree (canonical_id);


--
-- Name: ix_entity_aliases_id; Type: INDEX; Schema: public; Owner: news_user
--

CREATE INDEX ix_entity_aliases_id ON public.entity_aliases USING btree (id);


--
-- Name: ix_feed_items_feed_id; Type: INDEX; Schema: public; Owner: news_user
--

CREATE INDEX ix_feed_items_feed_id ON public.feed_items USING btree (feed_id);


--
-- Name: ix_feed_items_guid; Type: INDEX; Schema: public; Owner: news_user
--

CREATE INDEX ix_feed_items_guid ON public.feed_items USING btree (guid);


--
-- Name: ix_feed_items_link; Type: INDEX; Schema: public; Owner: news_user
--

CREATE INDEX ix_feed_items_link ON public.feed_items USING btree (link);


--
-- Name: ix_feed_items_published_at; Type: INDEX; Schema: public; Owner: news_user
--

CREATE INDEX ix_feed_items_published_at ON public.feed_items USING btree (published_at);


--
-- Name: ix_feed_items_source_id; Type: INDEX; Schema: public; Owner: news_user
--

CREATE INDEX ix_feed_items_source_id ON public.feed_items USING btree (source_id);


--
-- Name: ix_feed_items_source_published; Type: INDEX; Schema: public; Owner: news_user
--

CREATE INDEX ix_feed_items_source_published ON public.feed_items USING btree (source_id, published_at) WHERE (source_id IS NOT NULL);


--
-- Name: entity_aliases entity_aliases_canonical_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: news_user
--

ALTER TABLE ONLY public.entity_aliases
    ADD CONSTRAINT entity_aliases_canonical_id_fkey FOREIGN KEY (canonical_id) REFERENCES public.canonical_entities(id) ON DELETE CASCADE;


--
-- Name: feed_items feed_items_feed_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: news_user
--

ALTER TABLE ONLY public.feed_items
    ADD CONSTRAINT feed_items_feed_id_fkey FOREIGN KEY (feed_id) REFERENCES public.feeds(id) ON DELETE CASCADE;


--
-- Name: feed_items feed_items_parent_article_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: news_user
--

ALTER TABLE ONLY public.feed_items
    ADD CONSTRAINT feed_items_parent_article_id_fkey FOREIGN KEY (parent_article_id) REFERENCES public.feed_items(id) ON DELETE SET NULL;


--
-- Name: feed_items fk_feed_items_source_id; Type: FK CONSTRAINT; Schema: public; Owner: news_user
--

ALTER TABLE ONLY public.feed_items
    ADD CONSTRAINT fk_feed_items_source_id FOREIGN KEY (source_id) REFERENCES public.sources(id) ON DELETE SET NULL;


--
-- Name: TABLE entity_aliases; Type: ACL; Schema: public; Owner: news_user
--

GRANT ALL ON TABLE public.entity_aliases TO execution_user;


--
-- Name: SEQUENCE entity_aliases_id_seq; Type: ACL; Schema: public; Owner: news_user
--

GRANT ALL ON SEQUENCE public.entity_aliases_id_seq TO execution_user;


--
-- Name: TABLE feed_items; Type: ACL; Schema: public; Owner: news_user
--

GRANT ALL ON TABLE public.feed_items TO execution_user;


--
-- PostgreSQL database dump complete
--

\unrestrict 9K4dMansff3vWUHCE6IGAOv0WJs34h3g6gxfra7J7jdsxBlVgciIKtgK8lbLSU0

